from pathlib import Path
import numpy as np
import pandas as pd
import re

from .config import DATA_DIR, FILES, TARGET_YEAR


def resolve_data_dir(data_dir=None):
    return Path(data_dir) if data_dir else DATA_DIR


def file_path(key, data_dir=None):
    path = resolve_data_dir(data_dir) / FILES[key]
    if not path.exists():
        raise FileNotFoundError(f"ไม่พบไฟล์ {path}. กรุณาวางไฟล์ไว้ใน folder data/")
    return path


def dept3_from_deptcode(s):
    return pd.to_numeric(s, errors="coerce").astype("Int64") // 100


def first3_code(s):
    return (
        pd.to_numeric(s, errors="coerce")
        .astype("Int64")
        .astype(str)
        .str[:3]
        .replace("<NA>", np.nan)
        .astype("float")
        .astype("Int64")
    )


def load_damage(data_dir=None):
    raw = pd.read_excel(file_path("damage", data_dir))
    c0, c1 = raw.columns[:2]
    c2 = raw.columns[2] if len(raw.columns) >= 3 else None
    rows = []
    last_name = None

    for _, r in raw.iterrows():
        name = r.get(c0)
        v1 = pd.to_numeric(r.get(c1), errors="coerce")
        v2 = pd.to_numeric(r.get(c2), errors="coerce") if c2 else np.nan

        if pd.notna(name):
            last_name = str(name).strip()

        if pd.notna(v1) and pd.notna(name):
            rows.append({"key": str(name).strip(), "damage_probability": float(v1), "source_unit": None})

        if pd.notna(v2):
            unit_or_work = str(r.get(c1)).strip() if pd.notna(r.get(c1)) else None
            key = str(name).strip() if pd.notna(name) else f"{last_name}_{unit_or_work}"
            rows.append({"key": key, "damage_probability": float(v2), "source_unit": unit_or_work})

    return pd.DataFrame(rows).drop_duplicates("key")


def load_asset_quantities(data_dir=None):
    raw = pd.read_excel(file_path("group", data_dir), sheet_name="ASSET")
    df = raw[pd.to_numeric(raw["รหัส"], errors="coerce").notna()].copy()
    df["dept3"] = pd.to_numeric(df["รหัส"], errors="coerce").astype("Int64")

    count_cols = [
        "ท่อลอดทาง",
        "ท่อข้างทาง",
        "สะพานข้ามคลอง < 20 ม.",
        "สะพานลอยคนเดินข้าม",
        "ไฟสัญญาณจราจร",
        "ไฟคนเดินข้าม",
        "ไฟกระพริบ",
        "ไฟฟ้าแสงสว่าง",
        "ศาลาทางหลวง",
    ]

    df = df[["dept3", "หน่วยงาน"] + count_cols].copy()
    for c in count_cols:
        df[c] = pd.to_numeric(df[c].replace("-", 0), errors="coerce").fillna(0)

    df = df.rename(
        columns={
            "หน่วยงาน": "asset_district_name",
            "ท่อลอดทาง": "asset_culvert_underpass_num",
            "ท่อข้างทาง": "asset_roadside_pipe_num",
            "สะพานข้ามคลอง < 20 ม.": "asset_small_bridge_num",
            "สะพานลอยคนเดินข้าม": "asset_pedestrian_bridge_num",
            "ไฟสัญญาณจราจร": "asset_traffic_light_num",
            "ไฟคนเดินข้าม": "asset_ped_cross_light_num",
            "ไฟกระพริบ": "asset_flashing_light_num",
            "ไฟฟ้าแสงสว่าง": "asset_street_light_num",
            "ศาลาทางหลวง": "asset_pavilion_num",
        }
    )
    df["asset_drainage_pipe_num"] = df["asset_culvert_underpass_num"] + df["asset_roadside_pipe_num"]
    return df


def load_input_extras(data_dir=None):
    inp = pd.read_excel(file_path("group", data_dir), sheet_name="input")
    inp["dept3"] = first3_code(inp["depot_code"])

    sum_cols = [
        c
        for c in [
            "traffic_sign_num",
            "drainage_m",
            "roadsidepipe_m",
            "culvertpipe_m",
            "pipebridge_v",
            "pavilion_num",
            "building_num",
        ]
        if c in inp.columns
    ]
    mean_cols = [
        c
        for c in ["veh_total", "avg_iri", "elevation_mean", "elevation_var", "slope_mean", "slope_var"]
        if c in inp.columns
    ]

    agg = {c: "sum" for c in sum_cols}
    agg.update({c: "mean" for c in mean_cols})
    return inp.groupby("dept3", dropna=True).agg(agg).reset_index().add_prefix("input_").rename(columns={"input_dept3": "dept3"})


def load_district_base(data_dir=None):
    df = pd.read_excel(file_path("group", data_dir), sheet_name="group_data_final")
    df["dept3"] = pd.to_numeric(df["depot_code"], errors="coerce").astype("Int64")
    for c in df.columns:
        if c not in ["division_name", "district_name"]:
            df[c] = pd.to_numeric(df[c], errors="ignore")
    return df


def load_operating_distances(data_dir=None):
    df = pd.read_excel(file_path("operating_distances", data_dir))
    df["dept3"] = first3_code(df["depot_code"])
    return df.groupby("dept3", as_index=False)["total_distance_km"].sum().rename(columns={"total_distance_km": "operating_distance"})


def build_master(data_dir=None):
    group = load_district_base(data_dir)
    
    # Load bridge data and clean keys for merging
    try:
        bridge_df = pd.read_excel(file_path("bridge_bmms", data_dir))
        bridge_df["ความยาวสะพาน (ม.)"] = pd.to_numeric(bridge_df["ความยาวสะพาน (ม.)"], errors="coerce")
        bridge_grouped = bridge_df.groupby("แขวงการทาง")["ความยาวสะพาน (ม.)"].sum().reset_index()
        bridge_grouped.columns = ["district_name_bridge", "bridge_m"]

        def clean_name(name):
            if pd.isna(name): return name
            name = str(name)
            name = re.sub(r'\(.*?\)', '', name)
            name = name.replace(' ', '')
            name = name.replace('ขท.', 'แขวงทางหลวง')
            return name

        group["clean_key"] = group["district_name"].apply(clean_name)
        bridge_grouped["clean_key"] = bridge_grouped["district_name_bridge"].apply(clean_name)
        group = group.merge(bridge_grouped[["clean_key", "bridge_m"]], on="clean_key", how="left")
        group = group.drop(columns=["clean_key"])
    except Exception as e:
        print(f"Warning: Could not load bridge_bmms.xlsx: {e}")
        group["bridge_m"] = 0.0

    asset = load_asset_quantities(data_dir)
    input_extra = load_input_extras(data_dir)
    op_dist = load_operating_distances(data_dir)

    cluster = pd.read_excel(file_path("cluster", data_dir)).rename(columns={"deptcode_3": "dept3"})
    cluster["dept3"] = pd.to_numeric(cluster["dept3"], errors="coerce").astype("Int64")

    rmms = pd.read_excel(file_path("rmms", data_dir))
    rmms["dept3"] = dept3_from_deptcode(rmms["deptcode"])
    rmms68 = (
        rmms[rmms["budgetyear"].eq(TARGET_YEAR)]
        .groupby("dept3", as_index=False)
        .agg(
            machine_rental_cost=("รวมค่าเช่าเครื่องจักร", "sum"),
            rmms_total_budget=("รวมงบประมาณทั้งหมด", "sum"),
            rmms_workload_quantity=("ผลรวมปริมาณงาน", "sum"),
        )
    )

    master = (
        group.merge(asset, on="dept3", how="left")
        .merge(input_extra, on="dept3", how="left", suffixes=("", "_input"))
        .merge(cluster[["dept3", "Cluster"]], on="dept3", how="left")
        .merge(rmms68, on="dept3", how="left")
        .merge(op_dist[["dept3", "operating_distance"]], on="dept3", how="left")
    )
    master["hi_mast_num"] = 0.0

    for col in master.select_dtypes(include=["number"]).columns:
        master[col] = master[col].fillna(0)

    return master



def load_pavement_reference_from_damage(data_dir=None):
    """
    อ่านรายการงานซ่อมบำรุงถนนอ้างอิงจากไฟล์ข้อมูลโอกาสเกิดความเสียหาย
    section: 'ค่ามาตรฐานการซ่อมบำรุงถนนอ้างอิง'

    Output columns:
        - surface_type
        - workcode
        - workname
        - damage_probability
    """
    raw = pd.read_excel(file_path("damage", data_dir))

    c0 = raw.columns[0]
    c1 = raw.columns[1]
    c2 = raw.columns[2]

    start_idx = raw.index[
        raw[c0].astype(str).str.contains("ค่ามาตรฐานการซ่อมบำรุงถนนอ้างอิง", na=False)
    ]
    if len(start_idx) == 0:
        raise ValueError("ไม่พบ section 'ค่ามาตรฐานการซ่อมบำรุงถนนอ้างอิง' ในไฟล์ข้อมูลโอกาสเกิดความเสียหาย")

    pavement_raw = raw.loc[start_idx[0] + 1:].copy()

    rows = []
    current_surface_type = None
    last_workcode = None

    for _, r in pavement_raw.iterrows():
        v0 = r.get(c0)
        v1 = r.get(c1)
        v2 = r.get(c2)

        # ข้าม blank row
        if pd.isna(v0) and pd.isna(v1) and pd.isna(v2):
            continue

        # หัวกลุ่ม เช่น Asphalt / Concrete
        if isinstance(v0, str) and v0.strip() in ["Asphalt", "Concrete"]:
            current_surface_type = v0.strip()
            continue

        damage_probability = pd.to_numeric(v2, errors="coerce")
        if pd.isna(damage_probability):
            continue

        workcode = pd.to_numeric(v0, errors="coerce")
        if pd.notna(workcode):
            last_workcode = int(workcode)

        # หาก workcode เป็น blank จะอิงรหัสงานก่อนหน้า ตามรูปแบบตารางต้นทาง
        if last_workcode is None:
            continue

        workname = str(v1).strip() if pd.notna(v1) else None

        rows.append(
            {
                "surface_type": current_surface_type,
                "workcode": int(last_workcode),
                "workname": workname,
                "damage_probability": float(damage_probability),
            }
        )

    ref = pd.DataFrame(rows)
    if ref.empty:
        raise ValueError("อ่านรายการ pavement reference ไม่สำเร็จ กรุณาตรวจ format ไฟล์ damage")

    return ref


def load_rmms_unit_cost_by_workcode(data_dir=None, target_year=TARGET_YEAR):
    """
    อ่าน unit cost จาก RMMS เฉพาะปี target_year

    หลักการคำนวณ unit cost ต่อ workcode:
        weighted_unit_cost = sum(รวมงบประมาณทั้งหมด) / sum(ผลรวมปริมาณงาน)

    ถ้า quantity รวมเป็น 0 จะ fallback ไปใช้ mean ของ column 'unti cost'
    """
    rmms = pd.read_excel(file_path("rmms", data_dir))
    rmms = rmms[rmms["budgetyear"].eq(target_year)].copy()

    rmms["workcode"] = pd.to_numeric(rmms["workcode"], errors="coerce")
    rmms["quantity"] = pd.to_numeric(rmms["ผลรวมปริมาณงาน"], errors="coerce").fillna(0)
    rmms["total_budget"] = pd.to_numeric(rmms["รวมงบประมาณทั้งหมด"], errors="coerce").fillna(0)

    if "unti cost" in rmms.columns:
        rmms["unit_cost_raw"] = pd.to_numeric(rmms["unti cost"], errors="coerce")
    else:
        rmms["unit_cost_raw"] = np.nan

    rmms = rmms.dropna(subset=["workcode"])
    rmms["workcode"] = rmms["workcode"].astype(int)

    unit_cost = (
        rmms.groupby("workcode", as_index=False)
        .agg(
            rmms_quantity=("quantity", "sum"),
            rmms_total_budget=("total_budget", "sum"),
            rmms_unit_cost_mean=("unit_cost_raw", "mean"),
        )
    )

    unit_cost["rmms_unit_cost"] = np.where(
        unit_cost["rmms_quantity"] > 0,
        unit_cost["rmms_total_budget"] / unit_cost["rmms_quantity"],
        unit_cost["rmms_unit_cost_mean"],
    )

    return unit_cost[
        [
            "workcode",
            "rmms_quantity",
            "rmms_total_budget",
            "rmms_unit_cost_mean",
            "rmms_unit_cost",
        ]
    ]


def build_pavement_unit_cost_from_rmms(data_dir=None, target_year=TARGET_YEAR):
    """
    คำนวณ unit cost และ damage probability สำหรับ workload:
    'ผิวจราจร/ระยะทางต่อ 2 ช่องจราจร'

    Formula:
        pavement_unit_cost = sum(rmms_unit_cost ของทุกรายการใน section ค่ามาตรฐานการซ่อมบำรุงถนนอ้างอิง)

        pavement_damage_probability =
            sum(damage_probability_i * rmms_unit_cost_i) / sum(rmms_unit_cost_i)

    หมายเหตุ:
    - ใช้ RMMS เฉพาะปี 2568 ตาม TARGET_YEAR
    - ถ้า workcode ใดไม่มีใน RMMS ปี 2568 จะถือ unit cost = 0 และจะแสดงให้ตรวจใน detail
    """
    ref = load_pavement_reference_from_damage(data_dir)
    rmms_uc = load_rmms_unit_cost_by_workcode(data_dir, target_year=target_year)

    detail = ref.merge(rmms_uc, on="workcode", how="left")

    detail["rmms_unit_cost"] = pd.to_numeric(detail["rmms_unit_cost"], errors="coerce").fillna(0)
    detail["damage_probability"] = pd.to_numeric(detail["damage_probability"], errors="coerce").fillna(0)
    detail["weighted_probability_component"] = detail["damage_probability"] * detail["rmms_unit_cost"]

    #pavement_unit_cost = float(detail["rmms_unit_cost"].sum())
    pavement_unit_cost = 35000  # ใช้ค่า unit cost แบบไม่คูณ probability เพื่อให้เห็นงบประมาณที่ลงไปจริงๆ ตามสูตรที่ใช้ใน model

    if pavement_unit_cost > 0:
        pavement_damage_probability = float(detail["weighted_probability_component"].sum() / pavement_unit_cost)
    else:
        pavement_damage_probability = 0.0

    return {
        "pavement_unit_cost": pavement_unit_cost,
        "pavement_damage_probability": pavement_damage_probability,
        "detail": detail,
    }

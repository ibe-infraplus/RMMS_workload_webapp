import math
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.calculator import build_results, damage_lookup, get_dynamic_unit_cost_and_probability
from src.config import MAX_FACTOR_UPLIFT, WORKLOAD_CONFIG
from src.data_loader import build_master

app = FastAPI(
    title="RMMS Workload Cost API",
    description="""
API สำหรับคำนวณและจำลองผลกระทบต่องบประมาณบำรุงรักษาทางหลวงแบบ Real-time.
ระบบเปิดให้เรียกดูข้อมูลเริ่มต้น (Initial Data) และส่ง Parameter Grid เข้ามาคำนวณใหม่ได้ทันที.

**Endpoints:**
- `GET /api/init`: ดึงข้อมูลรายชื่อแขวง, Parameter Grid เริ่มต้น, และ Quantity ของแขวงที่ 1.
- `POST /api/calculate`: คำนวณงบประมาณใหม่ (Revised) เปรียบเทียบกับแบบเดิม (Baseline).
    """,
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache the master data locally
_master_cache = None

def get_master_data():
    global _master_cache
    if _master_cache is None:
        _master_cache = build_master("data")
    return _master_cache.copy()

def replace_nan(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if isinstance(obj, dict):
        return {k: replace_nan(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [replace_nan(i) for i in obj]
    return obj

@app.get("/api/init")
def get_initial_data():
    master = get_master_data()
    
    # Get district list
    master_view = master.copy()
    master_view["district_label"] = master_view["dept3"].astype(str) + " - " + master_view["district_name"].astype(str)
    master_view = master_view.sort_values(["division_name", "district_name"])
    
    districts = master_view[["dept3", "district_label", "division_name", "district_name"]].to_dict(orient="records")
    
    # Get parameter grid
    lookup = damage_lookup("data")
    param_grid = []
    for cfg in WORKLOAD_CONFIG:
        p, unit_cost = get_dynamic_unit_cost_and_probability(cfg, lookup, data_dir="data")
        param_grid.append({
            "workload_item": cfg.get("item", ""),
            "category": cfg.get("category", ""),
            "quantity_col": cfg.get("quantity_col", ""),
            "unit": cfg.get("unit", ""),
            "damage_probability": float(p) if not math.isnan(p) else 0.0,
            "unit_cost": float(unit_cost) if not math.isnan(unit_cost) else 0.0,
            "apply_damage_probability": bool(cfg.get("apply_damage_probability", True)),
            "note": cfg.get("note", ""),
            "condition_profile": cfg.get("condition_profile", "none"),
            "damage_key": cfg.get("damage_key")
        })

    # Default values from the first district
    selected_row = master.loc[master["dept3"].astype(int).eq(int(districts[0]["dept3"]))].iloc[0]
    default_quantities = {}
    for cfg in WORKLOAD_CONFIG:
        q_col = cfg["quantity_col"]
        if q_col:
            val = float(pd.to_numeric(pd.Series([selected_row.get(q_col, 0)]), errors="coerce").fillna(0).iloc[0])
            default_quantities[q_col] = val

    return {
        "districts": replace_nan(districts),
        "param_grid": replace_nan(param_grid),
        "max_factor_uplift": MAX_FACTOR_UPLIFT,
        "default_quantities": default_quantities,
        "master_columns": list(master.columns)
    }

FRAMEWORK_THAI_NAMES = {
    "pavement": "งานผิวทาง",
    "traffic": "งานจราจรสงเคราะห์",
    "drainage": "งานระบายน้ำ",
    "others": "งานเขตทางและอื่นๆ",
    "bridge": "งานสะพาน",
    "shoulder": "งานไหล่ทางและทางเชื่อม"
}

CATEGORY_MAPPING = {
    "ผิวจราจร/ระยะทางต่อ 2 ช่องจราจร": "pavement",
    "เกาะกลาง": "others",
    "สะพานลอยคนเดินข้าม": "bridge",
    "สะพานข้ามคลอง < 20 ม.": "bridge",
    "ท่อลอด": "bridge",
    "ศาลาทางหลวง": "others",
    "ไฟจราจร": "traffic",
    "ไฟทางข้าม": "traffic",
    "ไฟแสงสว่างกิ่งเดี่ยวกิ่งคู่": "traffic",
    "ไฟแสงสว่าง Hi-Mast": "traffic",
    "ไฟกระพริบ": "traffic",
    "ป้ายจราจร": "traffic",
    "ท่อระบายน้ำ": "drainage",
    "ทางระบายน้ำ": "drainage",
    "งานตัดหญ้าและบำรุงรักษาเขตทาง": "others"
}

def get_actual_category_breakdown(summary_row, detail_rows_df):
    actuals = {
        "pavement": 0.0,
        "traffic": 0.0,
        "drainage": 0.0,
        "others": 0.0,
        "bridge": 0.0,
        "shoulder": 0.0
    }
    
    for _, row in detail_rows_df.iterrows():
        item = row["workload_item"]
        cost = float(row.get("workload_plus_factor", 0.0))
        cat = CATEGORY_MAPPING.get(item, "others")
        if cat in actuals:
            actuals[cat] += cost
            
    return actuals

class CalculateRequest(BaseModel):
    selected_dept3: int = Field(..., description="รหัสแขวงทางหลวง (เช่น 100 for รหัสเต็ม 10000)")
    max_factor_uplift: float = Field(0.15, description="เพดานสูงสุดของ Scaling Factor (Condition Index)")
    use_damage_probability: bool = Field(True, description="เปิด/ปิดการคูณ Damage Probability")
    workload_overrides: Dict[str, Any] = Field(..., description="Map ของคอลัมน์ปริมาณงานที่ถูก Override ค่าความน่าจะเป็นและราคากลาง")
    quantity_updates: Dict[str, float] = Field(..., description="Map ของคอลัมน์ปริมาณงานที่ถูกกรอกแก้ไขตัวเลขใหม่")
    custom_config: Optional[List[Dict[str, Any]]] = Field(None, description="โครงสร้าง Parameter Grid ที่ถูกเพิ่ม/ลด/แก้ไข จากหน้าบ้าน")
    budget_multiplier: Optional[float] = Field(None, description="ตัวคูณร่วม X")
    budget_framework: Optional[Dict[str, float]] = Field(None, description="กรอบสัดส่วนงบประมาณ (เช่น {'pavement': 50.0, 'traffic': 15.0, ...})")


@app.get("/api/districts", tags=["Granular API"], summary="ดึงรายชื่อแขวงทางหลวงทั้งหมด")
def get_all_districts():
    master = get_master_data()
    master_view = master.copy()
    master_view["district_label"] = master_view["dept3"].astype(str) + " - " + master_view["district_name"].astype(str)
    master_view = master_view.sort_values(["division_name", "district_name"])
    districts = master_view[["dept3", "district_label", "division_name", "district_name"]].to_dict(orient="records")
    return {"districts": replace_nan(districts)}

@app.get("/api/districts/{dept3}", tags=["Granular API"], summary="ดึงข้อมูลตั้งต้น (Raw Quantities) ของแขวงที่ระบุ")
def get_district_raw_data(dept3: int):
    master = get_master_data()
    mask = master["dept3"].astype(int) == dept3
    if not any(mask):
        return {"error": "District not found"}
    row = master.loc[mask].iloc[0]
    
    quantities = {}
    for cfg in WORKLOAD_CONFIG:
        q_col = cfg.get("quantity_col")
        if q_col:
            val = float(pd.to_numeric(pd.Series([row.get(q_col, 0)]), errors="coerce").fillna(0).iloc[0])
            quantities[q_col] = val
            
    return {
        "dept3": dept3,
        "division_name": row.get("division_name"),
        "district_name": row.get("district_name"),
        "raw_attributes": {
            "length_to2": replace_nan(row.get("length_to2")),
            "aadt_w": replace_nan(row.get("aadt_w")),
            "iri_w": replace_nan(row.get("iri_w")),
            "machine_rental_cost": replace_nan(row.get("machine_rental_cost"))
        },
        "quantities": quantities
    }

@app.get("/api/config", tags=["Granular API"], summary="ดึงโครงสร้าง Parameter Grid ระดับประเทศ")
def get_global_config():
    lookup = damage_lookup("data")
    param_grid = []
    for cfg in WORKLOAD_CONFIG:
        p, unit_cost = get_dynamic_unit_cost_and_probability(cfg, lookup, data_dir="data")
        param_grid.append({
            "workload_item": cfg.get("item", ""),
            "category": cfg.get("category", ""),
            "quantity_col": cfg.get("quantity_col", ""),
            "unit": cfg.get("unit", ""),
            "damage_probability": float(p) if not math.isnan(p) else 0.0,
            "unit_cost": float(unit_cost) if not math.isnan(unit_cost) else 0.0,
            "apply_damage_probability": bool(cfg.get("apply_damage_probability", True)),
            "note": cfg.get("note", ""),
            "condition_profile": cfg.get("condition_profile", "none"),
            "damage_key": cfg.get("damage_key")
        })
    return {"param_grid": replace_nan(param_grid)}

@app.post("/api/calculate")
def calculate_workload(req: CalculateRequest):
    master = get_master_data()
    
    # Calculate baseline (no overrides, no quantity updates, static default configuration)
    base_summary, base_detail, base_master = build_results(
        master.copy(), "data", max_factor_uplift=0.15, use_damage_probability=True, workload_overrides={}, custom_config=None, budget_multiplier=req.budget_multiplier
    )

    # Calculate revised
    revised_master = master.copy()
    mask = revised_master["dept3"].astype(int) == req.selected_dept3
    for q_col, val in req.quantity_updates.items():
        if q_col in revised_master.columns:
            revised_master.loc[mask, q_col] = val

    revised_summary, revised_detail, revised_master_scored = build_results(
        revised_master, "data", req.max_factor_uplift, req.use_damage_probability, req.workload_overrides, custom_config=req.custom_config, budget_multiplier=req.budget_multiplier
    )

    # Extract pavement workload score from details
    pave_base = base_detail[base_detail["workload_item"].str.contains("ระยะทางต่อ 2 ช่องจราจร", na=False)][["dept3", "workload_score"]].rename(columns={"workload_score": "pavement_workload"})
    pave_rev = revised_detail[revised_detail["workload_item"].str.contains("ระยะทางต่อ 2 ช่องจราจร", na=False)][["dept3", "workload_score"]].rename(columns={"workload_score": "pavement_workload"})

    base_summary = base_summary.merge(pave_base, on="dept3", how="left").fillna({"pavement_workload": 0.0})
    revised_summary = revised_summary.merge(pave_rev, on="dept3", how="left").fillna({"pavement_workload": 0.0})

    base_one = base_summary[base_summary["dept3"].astype(int) == req.selected_dept3].iloc[0]
    revised_one = revised_summary[revised_summary["dept3"].astype(int) == req.selected_dept3].iloc[0]

    # Selected debug data
    debug_cols = [
        "dept3", "division_name", "district_name", "length_to2", "Cluster", 
        "traffic_score", "truck_score", "elevation_score", "rain_score", 
        "operating_distance", "operating_distance_score", "machine_rental_cost"
    ]
    debug_cols = [c for c in debug_cols if c in revised_master_scored.columns]
    debug_data = revised_master_scored.loc[mask, debug_cols].iloc[0].to_dict() if any(mask) else {}

    # Details for selected district
    detail_cols = [
        "workload_item", "category", "quantity", "unit", "damage_probability", 
        "unit_cost", "apply_damage_probability", "base_workload_cost", 
        "condition_profile", "factor_index_0_1", "factor_cost", "workload_plus_factor", "note"
    ]
    detail_cols = [c for c in detail_cols if c in revised_detail.columns]
    revised_detail_one = revised_detail[revised_detail["dept3"].astype(int) == req.selected_dept3][detail_cols]

    # Default quantities for the newly selected district (in case district changed)
    selected_row = master.loc[master["dept3"].astype(int).eq(req.selected_dept3)].iloc[0]
    default_quantities = {}
    for cfg in WORKLOAD_CONFIG:
        q_col = cfg["quantity_col"]
        if q_col:
            val = float(pd.to_numeric(pd.Series([selected_row.get(q_col, 0)]), errors="coerce").fillna(0).iloc[0])
            default_quantities[q_col] = val

    # Compute budget framework comparison
    base_detail_one = base_detail[base_detail["dept3"].astype(int) == req.selected_dept3]
    base_actuals = get_actual_category_breakdown(base_one, base_detail_one)
    revised_actuals = get_actual_category_breakdown(revised_one, revised_detail_one)
    
    fw_pct = req.budget_framework or {
        "pavement": 50.0,
        "traffic": 15.0,
        "drainage": 15.0,
        "others": 10.0,
        "bridge": 5.0,
        "shoulder": 5.0
    }
    
    framework_table = []
    total_base_budget = float(base_one["total_budget_model"])
    total_rev_budget = float(revised_one["total_budget_model"])
    
    for key, th_name in FRAMEWORK_THAI_NAMES.items():
        pct_target = fw_pct.get(key, 0.0)
        target_budget_base = total_base_budget * (pct_target / 100.0)
        target_budget_rev = total_rev_budget * (pct_target / 100.0)
        
        act_base = base_actuals.get(key, 0.0)
        act_rev = revised_actuals.get(key, 0.0)
        
        framework_table.append({
            "key": key,
            "category_name": th_name,
            "target_pct": pct_target,
            "baseline_target": target_budget_base,
            "baseline_actual": act_base,
            "baseline_diff": act_base - target_budget_base,
            "revised_target": target_budget_rev,
            "revised_actual": act_rev,
            "revised_diff": act_rev - target_budget_rev
        })

    # Prepare response
    res = {
        "framework_comparison": framework_table,
        "metrics": {
            "baseline_total": float(base_one["total_budget_model"]),
            "revised_total": float(revised_one["total_budget_model"]),
            "national_baseline": float(base_summary["total_budget_model"].sum()),
            "national_revised": float(revised_summary["total_budget_model"].sum()),
            "baseline_workload_score": float(base_one["workload_score"]),
            "revised_workload_score": float(revised_one["workload_score"]),
            "national_baseline_workload": float(base_summary["workload_score"].sum()),
            "national_revised_workload": float(revised_summary["workload_score"].sum()),
        },
        "breakdown": [
            {"component": "Base Workload", "baseline": float(base_one["base_workload_cost"]), "revised": float(revised_one["base_workload_cost"])},
            {"component": "Factor", "baseline": float(base_one["factor_cost"]), "revised": float(revised_one["factor_cost"])},
            {"component": "Total Budget", "baseline": float(base_one["total_budget_model"]), "revised": float(revised_one["total_budget_model"])},
        ],
        "workload_detail": revised_detail_one.to_dict(orient="records"),
        "debug": debug_data,
        "default_quantities": default_quantities,
        "chart_data": {
            "all_districts_baseline": base_summary[["dept3", "district_name", "total_budget_model", "workload_score", "pavement_workload"]].to_dict(orient="records"),
            "all_districts_revised": revised_summary[["dept3", "district_name", "total_budget_model", "division_name", "workload_score", "pavement_workload"]].to_dict(orient="records")
        },
        "summary_all": revised_summary.sort_values("total_budget_model", ascending=False)[[
            "dept3", "division_name", "district_name", "base_workload_cost", "factor_cost", "fixed_cost", "total_budget_model"
        ]].to_dict(orient="records")
    }

    return replace_nan(res)


@app.post("/api/export_excel")
def export_workload_excel(req: CalculateRequest):
    from fastapi.responses import StreamingResponse
    import io
    master = get_master_data()
    
    # 1. Calculate baseline (no overrides, no quantity updates)
    base_summary, base_detail, base_master = build_results(
        master.copy(), "data", max_factor_uplift=0.15, use_damage_probability=True, workload_overrides={}, custom_config=None, budget_multiplier=req.budget_multiplier
    )

    # 2. Calculate revised
    revised_master = master.copy()
    mask = revised_master["dept3"].astype(int) == req.selected_dept3
    for q_col, val in req.quantity_updates.items():
        if q_col in revised_master.columns:
            revised_master.loc[mask, q_col] = val

    revised_summary, revised_detail, revised_master_scored = build_results(
        revised_master, "data", req.max_factor_uplift, req.use_damage_probability, req.workload_overrides, custom_config=req.custom_config, budget_multiplier=req.budget_multiplier
    )

    # 3. Create Excel byte stream
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Sheet 1: Summary comparison
        # Let's combine baseline and revised summary
        summary_df = base_summary[["dept3", "division_name", "district_name", "workload_score", "machine_rental_cost", "grass_cost_estimate", "fixed_cost", "total_budget_model"]].copy()
        summary_df = summary_df.rename(columns={
            "workload_score": "baseline_workload_score",
            "machine_rental_cost": "baseline_machine_rental",
            "grass_cost_estimate": "baseline_grass_cutting",
            "fixed_cost": "baseline_fixed_cost",
            "total_budget_model": "baseline_total_budget"
        })
        
        rev_sub = revised_summary[["dept3", "workload_score", "machine_rental_cost", "grass_cost_estimate", "fixed_cost", "total_budget_model"]].copy()
        rev_sub = rev_sub.rename(columns={
            "workload_score": "revised_workload_score",
            "machine_rental_cost": "revised_machine_rental",
            "grass_cost_estimate": "revised_grass_cutting",
            "fixed_cost": "revised_fixed_cost",
            "total_budget_model": "revised_total_budget"
        })
        
        comparison = summary_df.merge(rev_sub, on="dept3", how="inner")
        # Add difference columns
        comparison["workload_score_diff"] = comparison["revised_workload_score"] - comparison["baseline_workload_score"]
        comparison["total_budget_diff"] = comparison["revised_total_budget"] - comparison["baseline_total_budget"]
        comparison.to_excel(writer, index=False, sheet_name="Summary_Comparison")
        
        # Sheet 2: Revised Detail for Selected District
        sel_row = revised_summary[revised_summary["dept3"].astype(int) == req.selected_dept3]
        if not sel_row.empty:
            sel_name = str(sel_row.iloc[0]["district_name"])
            # Excel sheet name limit is 31 chars
            sheet_name = f"Detail_{req.selected_dept3}_{sel_name}"[:30]
        else:
            sheet_name = f"Detail_{req.selected_dept3}"
        
        revised_detail_selected = revised_detail[revised_detail["dept3"].astype(int) == req.selected_dept3].copy()
        revised_detail_selected.to_excel(writer, index=False, sheet_name=sheet_name)

        # Sheet 3: Detailed Workload (All)
        revised_detail.to_excel(writer, index=False, sheet_name="Revised_Detail_All")
        
        # Sheet 3: Parameters
        if req.custom_config:
            param_df = pd.DataFrame(req.custom_config)
        else:
            # Fallback to current configurations
            param_grid = []
            lookup = damage_lookup("data")
            for cfg in WORKLOAD_CONFIG:
                p, unit_cost = get_dynamic_unit_cost_and_probability(cfg, lookup, data_dir="data")
                # Apply overrides if present
                q_col = cfg.get("quantity_col", "")
                if q_col in req.workload_overrides:
                    p = req.workload_overrides[q_col].get("damage_probability", p)
                    unit_cost = req.workload_overrides[q_col].get("unit_cost", unit_cost)
                    apply_dp = req.workload_overrides[q_col].get("apply_damage_probability", cfg.get("apply_damage_probability", True))
                else:
                    apply_dp = cfg.get("apply_damage_probability", True)
                param_grid.append({
                    "workload_item": cfg.get("item", ""),
                    "category": cfg.get("category", ""),
                    "quantity_col": q_col,
                    "unit": cfg.get("unit", ""),
                    "damage_probability": p,
                    "unit_cost": unit_cost,
                    "apply_damage_probability": apply_dp
                })
            param_df = pd.DataFrame(param_grid)
        param_df.to_excel(writer, index=False, sheet_name="Parameter_Grid")

        # Sheet 5: Budget Framework Comparison (Selected District)
        base_one_ex = base_summary[base_summary["dept3"].astype(int) == req.selected_dept3].iloc[0]
        rev_one_ex = revised_summary[revised_summary["dept3"].astype(int) == req.selected_dept3].iloc[0]
        base_detail_ex = base_detail[base_detail["dept3"].astype(int) == req.selected_dept3]
        rev_detail_ex = revised_detail[revised_detail["dept3"].astype(int) == req.selected_dept3]
        
        base_actuals_ex = get_actual_category_breakdown(base_one_ex, base_detail_ex)
        rev_actuals_ex = get_actual_category_breakdown(rev_one_ex, rev_detail_ex)
        
        fw_pct = req.budget_framework or {
            "pavement": 50.0,
            "traffic": 15.0,
            "drainage": 15.0,
            "others": 10.0,
            "bridge": 5.0,
            "shoulder": 5.0
        }
        
        fw_rows = []
        for key, th_name in FRAMEWORK_THAI_NAMES.items():
            pct_target = fw_pct.get(key, 0.0)
            target_base = float(base_one_ex["total_budget_model"]) * (pct_target / 100.0)
            target_rev = float(rev_one_ex["total_budget_model"]) * (pct_target / 100.0)
            act_base = base_actuals_ex.get(key, 0.0)
            act_rev = rev_actuals_ex.get(key, 0.0)
            
            fw_rows.append({
                "หมวดหมู่งาน": th_name,
                "สัดส่วนเป้าหมาย (%)": pct_target,
                "งบประมาณเป้าหมาย Baseline (บาท)": target_base,
                "งบประมาณคำนวณจริง Baseline (บาท)": act_base,
                "ส่วนต่าง Baseline (บาท)": act_base - target_base,
                "งบประมาณเป้าหมาย Revised (บาท)": target_rev,
                "งบประมาณคำนวณจริง Revised (บาท)": act_rev,
                "ส่วนต่าง Revised (บาท)": act_rev - target_rev
            })
        fw_df = pd.DataFrame(fw_rows)
        fw_df.to_excel(writer, index=False, sheet_name="Budget_Framework")

    output.seek(0)
    
    headers = {
        'Content-Disposition': 'attachment; filename="revised_workload_cost_model.xlsx"'
    }
    return StreamingResponse(
        output,
        headers=headers,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

class SingleCalculateRequest(BaseModel):
    max_factor_uplift: float = Field(0.15, description="เพดานสูงสุดของ Scaling Factor (Condition Index)")
    use_damage_probability: bool = Field(True, description="เปิด/ปิดการคูณ Damage Probability")
    workload_overrides: Optional[Dict[str, Any]] = Field(None, description="Map ของคอลัมน์ปริมาณงานที่ถูก Override ค่าความน่าจะเป็นและราคากลาง")
    quantity_updates: Optional[Dict[str, float]] = Field(None, description="Map ของคอลัมน์ปริมาณงานที่ถูกกรอกแก้ไขตัวเลขใหม่")
    custom_config: Optional[List[Dict[str, Any]]] = Field(None, description="โครงสร้าง Parameter Grid ที่ถูกเพิ่ม/ลด/แก้ไข จากหน้าบ้าน")

@app.post("/api/calculate/{dept3}", tags=["Granular API"], summary="ทดสอบคำนวณงบประมาณเฉพาะแขวงที่ระบุ")
def calculate_single_district(dept3: int, req: SingleCalculateRequest):
    master = get_master_data()
    mask = master["dept3"].astype(int) == dept3
    if not any(mask):
        return {"error": "District not found"}
        
    workload_overrides = req.workload_overrides or {}
    quantity_updates = req.quantity_updates or {}
    
    revised_master = master.copy()
    for q_col, val in quantity_updates.items():
        if q_col in revised_master.columns:
            revised_master.loc[mask, q_col] = val

    revised_summary, revised_detail, revised_master_scored = build_results(
        revised_master, "data", req.max_factor_uplift, req.use_damage_probability, workload_overrides, custom_config=req.custom_config
    )

    revised_one = revised_summary[revised_summary["dept3"].astype(int) == dept3].iloc[0]
    
    detail_cols = [
        "workload_item", "category", "quantity", "unit", "damage_probability", 
        "unit_cost", "apply_damage_probability", "base_workload_cost", 
        "condition_profile", "factor_index_0_1", "factor_cost", "workload_plus_factor", "note"
    ]
    detail_cols = [c for c in detail_cols if c in revised_detail.columns]
    revised_detail_one = revised_detail[revised_detail["dept3"].astype(int) == dept3][detail_cols]

    res = {
        "dept3": dept3,
        "district_name": revised_one.get("district_name"),
        "total_budget_model": float(revised_one["total_budget_model"]),
        "breakdown": [
            {"component": "Base Workload", "cost": float(revised_one["base_workload_cost"])},
            {"component": "Factor", "cost": float(revised_one["factor_cost"])},
        ],
        "workload_detail": revised_detail_one.to_dict(orient="records")
    }
    
    return replace_nan(res)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)

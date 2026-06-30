from pathlib import Path

TARGET_YEAR = 2568
MAX_FACTOR_UPLIFT = 0.15
DEFAULT_CAP_LIMIT = 6_000_000_000

DATA_DIR = Path("data")
FILES = {
    "damage": "ข้อมูลโอกาสเกิดความเสียหาย (1).xlsx",
    "rmms": "แผนงาน RMMS.xlsx",
    "cluster": "cluster_district.xlsx",
    "group": "group_data_final.xlsx",
    "operating_distances": "operating_distances.xlsx",
    "bridge_bmms": "bridge_bmms.xlsx",
}

CLUSTER_GRASS_FORMULA = {
    0: {"slope": 7623.5896, "intercept": 1915806.6067},
    1: {"slope": 10742.3944, "intercept": 7303610.9973},
    2: {"slope": 28697.5085, "intercept": 2988185.5760},
}

# สูตรหลัก: quantity * damage_probability * unit_cost + factor + fixed cost
# สามารถแก้ quantity_col, damage_probability, unit_cost, factor profile ได้ที่นี่
WORKLOAD_CONFIG = [
    {
        "item": "ผิวจราจร/ระยะทางต่อ 2 ช่องจราจร",
        "category": "Pavement",
        "quantity_col": "length_to2",
        "unit": "กม.",
        "damage_key": None,
        "damage_probability": None,
        "unit_cost": None,
        "apply_damage_probability": False,
        "condition_profile": "pavement",
        "note": (
            "unit cost คำนวณอัตโนมัติจาก "
            "'ค่ามาตรฐานการซ่อมบำรุงถนนอ้างอิง' ในไฟล์ข้อมูลโอกาสเกิดความเสียหาย "
            "แล้ว join unit cost จาก RMMS ปี 2568 โดยไม่คูณ damage probability สำหรับผิวจราจร"
        ),
    },
    {
        "item": "สะพานลอยคนเดินข้าม",
        "category": "Asset",
        "quantity_col": "asset_pedestrian_bridge_num",
        "unit": "แห่ง",
        "damage_key": "สะพานลอยคนเดิน",
        "unit_cost": 5000,
        "condition_profile": "bridge",
        "note": "จาก ASSET",
    },
    {
        "item": "สะพานข้ามคลอง < 20 ม.",
        "category": "Asset",
        "quantity_col": "bridge_m",
        "unit": "เมตร",
        "damage_key": "สะพานทางยกระดับ",
        "unit_cost": 137.16,
        "condition_profile": "bridge",
        "note": "ใช้คอลัมน์ใหม่ bridge_m (หน่วยเป็นเมตร)",
    },
    {
        "item": "ท่อลอด",
        "category": "Asset",
        "quantity_col": "input_pipebridge_v",
        "unit": "แห่ง/ช่อง",
        "damage_key": "สะพานทางยกระดับ",
        "unit_cost": 500,
        "condition_profile": "bridge",
        "note": "ถ้าไม่มีข้อมูล pipebridge_v จะเป็น 0",
    },
    {
        "item": "ศาลาทางหลวง",
        "category": "Asset",
        "quantity_col": "asset_pavilion_num",
        "unit": "แห่ง",
        "damage_key": "ศาลา",
        "unit_cost": 3000,
        "condition_profile": "none",
        "note": "จาก ASSET",
    },
    {
        "item": "ไฟจราจร",
        "category": "Asset",
        "quantity_col": "asset_traffic_light_num",
        "unit": "ต้น",
        "damage_key": "ไฟจราจร",
        "unit_cost": 40000,
        "condition_profile": "traffic_asset",
        "note": "ใช้ probability หน่วยต้น",
    },
    {
        "item": "ไฟทางข้าม",
        "category": "Asset",
        "quantity_col": "asset_ped_cross_light_num",
        "unit": "ชุด",
        "damage_key": "ไฟทางข้าม",
        "unit_cost": 500,
        "condition_profile": "traffic_asset",
        "note": "จาก ASSET ไฟคนเดินข้าม",
    },
    {
        "item": "ไฟแสงสว่างกิ่งเดี่ยวกิ่งคู่",
        "category": "Asset",
        "quantity_col": "asset_street_light_num",
        "unit": "ต้น",
        "damage_key": "ไฟแสงสว่างกิ่งเดี่ยวกิ่งคู่",
        "unit_cost": 100,
        "condition_profile": "traffic_asset",
        "note": "จาก ASSET ไฟฟ้าแสงสว่าง",
    },
    {
        "item": "ไฟแสงสว่าง Hi-Mast",
        "category": "Asset",
        "quantity_col": "hi_mast_num",
        "unit": "ต้น",
        "damage_key": "ไฟแสงสว่าง Hi-Mast",
        "unit_cost": 100,
        "condition_profile": "traffic_asset",
        "note": "ไม่มีคอลัมน์ตรงในไฟล์ ตั้ง default = 0 ให้ user กรอกใน web app",
    },
    {
        "item": "ไฟกระพริบ",
        "category": "Asset",
        "quantity_col": "asset_flashing_light_num",
        "unit": "ชุด",
        "damage_key": "ไฟกระพริบ",
        "unit_cost": 500,
        "condition_profile": "traffic_asset",
        "note": "จาก ASSET",
    },
    {
        "item": "ป้ายจราจร",
        "category": "Asset",
        "quantity_col": "input_traffic_sign_num",
        "unit": "ป้าย",
        "damage_key": "ป้ายจราจร",
        "unit_cost": 0,
        "condition_profile": "traffic_asset",
        "note": "unit cost ไม่มีในไฟล์ราคาต้นทุน กรุณาเติมใน CONFIG",
    },
    {
        "item": "ท่อระบายน้ำ",
        "category": "Asset",
        "quantity_col": "asset_drainage_pipe_num",
        "unit": "แห่ง",
        "damage_key": "ท่อระบายน้ำ",
        "unit_cost": 350,
        "condition_profile": "drainage",
        "note": "รวมท่อลอดทางและท่อข้างทาง",
    },
    {
        "item": "ทางระบายน้ำ",
        "category": "Asset",
        "quantity_col": "input_drainage_m",
        "unit": "เมตร",
        "damage_key": "ท่อระบายน้ำ",
        "unit_cost": 0,
        "condition_profile": "drainage",
        "note": "มี quantity แต่ยังไม่มี unit cost",
    },
    {
        "item": "ค่าบำรุงจุดกางเต็นท์",
        "category": "Policy",
        "quantity_col": "จำนวนจุดกางเต็นท์",
        "unit": "แห่ง",
        "damage_key": None,
        "damage_probability": 1.0,
        "unit_cost": 300000,
        "condition_profile": "none",
        "note": "งานนโยบาย ใช้ probability=1",
    },
    {
        "item": "ค่าบำรุงจุดพักรถ",
        "category": "Policy",
        "quantity_col": "จำนวนจุดพักรถ",
        "unit": "แห่ง",
        "damage_key": None,
        "damage_probability": 1.0,
        "unit_cost": 300000,
        "condition_profile": "traffic_asset",
        "note": "งานนโยบาย ใช้ probability=1",
    },
    {
        "item": "ค่าบำรุงภูมิสถาปัตย์",
        "category": "Policy",
        "quantity_col": "จำนวนภูมิสถาปัตย์",
        "unit": "แห่ง",
        "damage_key": None,
        "damage_probability": 1.0,
        "unit_cost": 300000,
        "condition_profile": "rain_only",
        "note": "งานนโยบาย ใช้ probability=1",
    },
]

FACTOR_PROFILES = {
    "none": {},
    "pavement": {"traffic_score": 0.30, "truck_score": 0.25, "elevation_score": 0.15, "rain_score": 0.20, "operating_distance_score": 0.10},
    "bridge": {"traffic_score": 0.25, "truck_score": 0.30, "elevation_score": 0.25, "rain_score": 0.10, "operating_distance_score": 0.10},
    "drainage": {"traffic_score": 0.15, "truck_score": 0.00, "elevation_score": 0.20, "rain_score": 0.55, "operating_distance_score": 0.10},
    "traffic_asset": {"traffic_score": 0.50, "truck_score": 0.20, "elevation_score": 0.00, "rain_score": 0.20, "operating_distance_score": 0.10},
    "rain_only": {"rain_score": 1.00},
}

import math
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.calculator import build_results, damage_lookup, get_dynamic_unit_cost_and_probability
from src.config import MAX_FACTOR_UPLIFT, WORKLOAD_CONFIG
from src.data_loader import build_master

app = FastAPI(title="Workload Cost API")

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

class CalculateRequest(BaseModel):
    selected_dept3: int
    max_factor_uplift: float
    use_damage_probability: bool
    workload_overrides: Dict[str, Any]
    quantity_updates: Dict[str, float]
    custom_config: Optional[list] = None

@app.post("/api/calculate")
def calculate_workload(req: CalculateRequest):
    master = get_master_data()
    
    # Calculate baseline (no overrides, no quantity updates)
    base_summary, base_detail, base_master = build_results(
        master.copy(), "data", req.max_factor_uplift, req.use_damage_probability, {}, custom_config=req.custom_config
    )

    # Calculate revised
    revised_master = master.copy()
    mask = revised_master["dept3"].astype(int) == req.selected_dept3
    for q_col, val in req.quantity_updates.items():
        if q_col in revised_master.columns:
            revised_master.loc[mask, q_col] = val

    revised_summary, revised_detail, revised_master_scored = build_results(
        revised_master, "data", req.max_factor_uplift, req.use_damage_probability, req.workload_overrides, custom_config=req.custom_config
    )

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

    # Prepare response
    res = {
        "metrics": {
            "baseline_total": float(base_one["total_budget_model"]),
            "revised_total": float(revised_one["total_budget_model"]),
            "national_baseline": float(base_summary["total_budget_model"].sum()),
            "national_revised": float(revised_summary["total_budget_model"].sum()),
        },
        "breakdown": [
            {"component": "Base Workload", "baseline": float(base_one["base_workload_cost"]), "revised": float(revised_one["base_workload_cost"])},
            {"component": "Factor", "baseline": float(base_one["factor_cost"]), "revised": float(revised_one["factor_cost"])},
            {"component": "Fixed Cost: ค่าเช่าเครื่องจักร", "baseline": float(base_one["machine_rental_cost"]), "revised": float(revised_one["machine_rental_cost"])},
            {"component": "Fixed Cost: งานตัดหญ้า", "baseline": float(base_one["grass_cost_estimate"]), "revised": float(revised_one["grass_cost_estimate"])},
            {"component": "Total Budget", "baseline": float(base_one["total_budget_model"]), "revised": float(revised_one["total_budget_model"])},
        ],
        "workload_detail": revised_detail_one.to_dict(orient="records"),
        "debug": debug_data,
        "default_quantities": default_quantities,
        "chart_data": {
            "all_districts_baseline": base_summary[["dept3", "district_name", "total_budget_model"]].to_dict(orient="records"),
            "all_districts_revised": revised_summary[["dept3", "district_name", "total_budget_model", "division_name"]].to_dict(orient="records")
        },
        "summary_all": revised_summary.sort_values("total_budget_model", ascending=False)[[
            "dept3", "division_name", "district_name", "base_workload_cost", "factor_cost", "fixed_cost", "total_budget_model"
        ]].to_dict(orient="records")
    }

    return replace_nan(res)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

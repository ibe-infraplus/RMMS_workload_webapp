import numpy as np
import pandas as pd

from .config import CLUSTER_GRASS_FORMULA, FACTOR_PROFILES, MAX_FACTOR_UPLIFT, WORKLOAD_CONFIG
from .data_loader import load_damage, build_pavement_unit_cost_from_rmms


def percentile_score(series):
    x = pd.to_numeric(series, errors="coerce")
    if x.notna().sum() == 0:
        return pd.Series(0.0, index=series.index)
    return x.rank(pct=True).fillna(0)


def add_condition_scores(master):
    out = master.copy()
    veh = out["veh_total"] if "veh_total" in out else out.get("input_veh_total", 0)
    out["traffic_score"] = percentile_score(veh)

    heavy_col = next((c for c in ["truck_total", "heavy_truck", "truck_volume", "ปริมาณรถบรรทุกหนัก"] if c in out.columns), None)
    out["truck_score"] = percentile_score(out[heavy_col]) if heavy_col else out["traffic_score"] * 0.70

    elev_inputs = []
    for c in ["elevation_var", "slope_var", "slope_mean", "input_elevation_var", "input_slope_var", "input_slope_mean"]:
        if c in out.columns:
            elev_inputs.append(percentile_score(out[c].abs() if "slope_mean" in c else out[c]))
    out["elevation_score"] = pd.concat(elev_inputs, axis=1).mean(axis=1) if elev_inputs else 0
    out["rain_score"] = percentile_score(out["พื้นที่ฝนชุก"]) if "พื้นที่ฝนชุก" in out else 0
    out["operating_distance_score"] = percentile_score(out["operating_distance"]) if "operating_distance" in out else 0
    return out


def damage_lookup(data_dir=None):
    df = load_damage(data_dir)
    if df.empty:
        return {}
    return df.set_index("key")["damage_probability"].to_dict()


def get_damage_probability(cfg, lookup):
    if "damage_probability" in cfg and cfg["damage_probability"] is not None:
        return float(cfg["damage_probability"])
    key = cfg.get("damage_key")
    val = lookup.get(key, np.nan)
    return 1.0 if pd.isna(val) else float(val)


def get_dynamic_unit_cost_and_probability(cfg, lookup, data_dir=None):
    """
    คืนค่า damage_probability และ unit_cost ตามประเภท workload
    """
    item = cfg.get("item", "")
    if "ตัดหญ้า" in item:
        return 1.0, 10742.3944

    p = get_damage_probability(cfg, lookup)
    unit_cost = float(cfg.get("unit_cost", 0) or 0)
    return p, unit_cost


def compute_workload(
    master,
    data_dir=None,
    max_factor_uplift=MAX_FACTOR_UPLIFT,
    use_damage_probability=True,
    workload_overrides=None,
    custom_config=None,
    budget_multiplier=None,
):
    master = add_condition_scores(master)
    lookup = damage_lookup(data_dir)
    details = []

    override_map = {}
    if isinstance(workload_overrides, dict):
        override_map = workload_overrides

    config_to_use = custom_config if custom_config is not None else WORKLOAD_CONFIG

    # Calculate dynamic unit costs and find the minimum non-zero unit cost
    resolved_costs = []
    for cfg in config_to_use:
        p, unit_cost = get_dynamic_unit_cost_and_probability(cfg, lookup, data_dir=data_dir)
        q_col = cfg.get("quantity_col", "")
        item = cfg.get("item", "")
        ov = override_map.get(item, override_map.get(q_col, {})) if isinstance(override_map, dict) else {}
        if isinstance(ov, dict) and "unit_cost" in ov and ov["unit_cost"] is not None:
            unit_cost = float(ov["unit_cost"])
        resolved_costs.append(unit_cost)
    
    non_zero_costs = [c for c in resolved_costs if isinstance(c, (int, float)) and c > 0]
    min_unit_cost = min(non_zero_costs) if non_zero_costs else 1.0

    if budget_multiplier is None:
        budget_multiplier = min_unit_cost

    for cfg in config_to_use:
        q_col = cfg.get("quantity_col", "")
        item = cfg.get("item", "")
        q = pd.to_numeric(master[q_col], errors="coerce").fillna(0) if q_col and q_col in master.columns else pd.Series(0, index=master.index)
        if "งานตัดหญ้า" in item:
            sidewalk_km = pd.to_numeric(master["sidewalk_sqm"], errors="coerce").fillna(0) / 1000.0
            q = (q - sidewalk_km).clip(lower=0)
        p, unit_cost = get_dynamic_unit_cost_and_probability(cfg, lookup, data_dir=data_dir)
        ov = override_map.get(item, override_map.get(q_col, {})) if isinstance(override_map, dict) else {}
        if isinstance(ov, dict):
            if "damage_probability" in ov and ov["damage_probability"] is not None:
                p = float(ov["damage_probability"])
            if "unit_cost" in ov and ov["unit_cost"] is not None:
                unit_cost = float(ov["unit_cost"])
            apply_cfg = ov.get("apply_damage_probability", cfg.get("apply_damage_probability", True))
        else:
            apply_cfg = cfg.get("apply_damage_probability", True)

        # Dynamic Unit Cost for Grass Cutting
        if "งานตัดหญ้า" in item:
            is_overridden = False
            if isinstance(ov, dict) and "unit_cost" in ov and ov["unit_cost"] is not None:
                if abs(float(ov["unit_cost"]) - 10742.3944) > 1e-4:
                    is_overridden = True
                    unit_cost = float(ov["unit_cost"])
            if not is_overridden:
                unit_cost = master["Cluster"].map(lambda c: CLUSTER_GRASS_FORMULA.get(int(c), {}).get("slope", 0.0)).fillna(0.0)

        # 1. Base Value
        if isinstance(unit_cost, pd.Series):
            base_value = unit_cost / min_unit_cost
        else:
            base_value = float(unit_cost / min_unit_cost) if unit_cost > 0 else 0.0

        # 2. Workload Unit
        workload_unit = q * base_value

        # 3. Workload Score
        apply_damage_probability = bool(apply_cfg) and bool(use_damage_probability)
        if apply_damage_probability:
            workload_score = workload_unit * p
        else:
            workload_score = workload_unit

        # 4. Workload Cost (Base Cost in Baht)
        base_cost = workload_score * budget_multiplier

        profile = cfg.get("condition_profile", "none")
        weights = FACTOR_PROFILES.get(profile, {})
        if weights:
            factor_index = sum(master[k] * w for k, w in weights.items() if k in master.columns)
        else:
            factor_index = pd.Series(0.0, index=master.index)

        factor_cost = base_cost * max_factor_uplift * factor_index
        details.append(
            pd.DataFrame(
                {
                    "dept3": master["dept3"],
                    "division_name": master["division_name"],
                    "district_name": master["district_name"],
                    "workload_item": cfg["item"],
                    "category": cfg["category"],
                    "quantity": q,
                    "unit": cfg["unit"],
                    "damage_probability": p,
                    "unit_cost": unit_cost,
                    "apply_damage_probability": apply_damage_probability,
                    "base_value": base_value,
                    "total_quantity": float(q.sum()),
                    "workload_unit": workload_unit,
                    "workload_score": workload_score,
                    "base_workload_cost": base_cost,
                    "condition_profile": profile,
                    "factor_index_0_1": factor_index,
                    "factor_cost": factor_cost,
                    "workload_plus_factor": base_cost + factor_cost,
                    "note": cfg.get("note", ""),
                }
            )
        )
    return pd.concat(details, ignore_index=True), master


def compute_fixed_cost(master):
    out = master[["dept3", "district_name"]].copy()
    out["machine_rental_cost"] = 0.0
    out["grass_cost_estimate"] = 0.0
    out["fixed_cost"] = 0.0
    return out


def build_results(
    master,
    data_dir=None,
    max_factor_uplift=MAX_FACTOR_UPLIFT,
    use_damage_probability=True,
    workload_overrides=None,
    custom_config=None,
    budget_multiplier=None,
):
    details, master_scored = compute_workload(
        master,
        data_dir=data_dir,
        max_factor_uplift=max_factor_uplift,
        use_damage_probability=use_damage_probability,
        workload_overrides=workload_overrides,
        custom_config=custom_config,
        budget_multiplier=budget_multiplier,
    )
    fixed = compute_fixed_cost(master_scored)

    summary = (
        details.groupby(["dept3", "division_name", "district_name"], as_index=False)
        .agg(
            workload_score=("workload_score", "sum"),
            base_workload_cost=("base_workload_cost", "sum"),
            factor_cost=("factor_cost", "sum"),
            workload_plus_factor=("workload_plus_factor", "sum"),
        )
    )
    summary = summary.merge(fixed[["dept3", "machine_rental_cost", "grass_cost_estimate", "fixed_cost"]], on="dept3", how="left")
    summary["total_budget_model"] = summary["workload_plus_factor"] + summary["fixed_cost"]

    compare_cols = [
        "dept3",
        "sum_งบแผน68",
        "rmms_total_budget",
        "rmms_workload_quantity",
        "Cluster",
        "length_to2",
        "traffic_score",
        "truck_score",
        "rain_score",
        "elevation_score",
        "operating_distance_score",
    ]
    compare_cols = [c for c in compare_cols if c in master_scored.columns]
    summary = summary.merge(master_scored[compare_cols], on="dept3", how="left")
    return summary, details, master_scored


def apply_cap(summary, cap_limit):
    out = summary.copy()
    national_total = float(out["total_budget_model"].sum())
    cap_ratio = min(1.0, cap_limit / national_total) if national_total > 0 else 1.0
    out["cap_limit"] = cap_limit
    out["national_total_before_cap"] = national_total
    out["cap_ratio"] = cap_ratio
    out["budget_after_cap"] = out["total_budget_model"] * cap_ratio
    out["budget_reduction"] = out["total_budget_model"] - out["budget_after_cap"]
    return out, national_total, cap_ratio

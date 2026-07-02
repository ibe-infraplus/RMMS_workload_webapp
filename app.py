import pandas as pd
import plotly.express as px
import streamlit as st

from src.calculator import build_results, damage_lookup, get_dynamic_unit_cost_and_probability
from src.config import MAX_FACTOR_UPLIFT, WORKLOAD_CONFIG
from src.data_loader import build_master, build_pavement_unit_cost_from_rmms

st.set_page_config(
    page_title="Workload Cost Calculation",
    page_icon="🛣️",
    layout="wide",
)


# =========================================================
# Helper functions
# =========================================================

def baht(x):
    try:
        return f"{float(x):,.0f} บาท"
    except Exception:
        return "-"


def show_budget_donut_chart(df_summary: pd.DataFrame):
    """
    Donut chart แสดงสัดส่วนงบประมาณของทุกแขวงจาก total_budget_model
    Required columns:
        - district_name
        - total_budget_model
    Optional columns:
        - dept3
        - division_name
    """
    df_chart = df_summary.copy()
    required_cols = ["district_name", "total_budget_model"]
    missing = [c for c in required_cols if c not in df_chart.columns]
    if missing:
        st.warning(f"ไม่สามารถสร้าง donut chart ได้ เพราะขาด column: {missing}")
        return

    df_chart["district_name"] = df_chart["district_name"].fillna("ไม่ระบุแขวง")
    df_chart["total_budget_model"] = pd.to_numeric(df_chart["total_budget_model"], errors="coerce").fillna(0)
    df_chart = df_chart[df_chart["total_budget_model"] > 0].copy()
    if df_chart.empty:
        st.info("ไม่มีข้อมูลงบประมาณสำหรับสร้าง donut chart")
        return

    df_chart = df_chart.sort_values("total_budget_model", ascending=False)
    total_budget_all = float(df_chart["total_budget_model"].sum())

    st.subheader("ภาพรวมสัดส่วนงบประมาณที่ลงไปในแต่ละแขวง")
    st.caption("Donut chart นี้แสดงสัดส่วนงบประมาณของแต่ละแขวงจาก Revised Total Budget หลังจากปรับ quantity แล้ว")

    c1, c2, c3 = st.columns(3)
    n_district = int(df_chart["district_name"].nunique())
    c1.metric("งบประมาณรวมทุกแขวง", baht(total_budget_all))
    c2.metric("จำนวนแขวง", f"{n_district:,.0f} แขวง")
    c3.metric("งบเฉลี่ยต่อแขวง", baht(total_budget_all / max(n_district, 1)))

    if "dept3" in df_chart.columns:
        df_chart["district_label"] = df_chart["dept3"].astype(str) + " - " + df_chart["district_name"].astype(str)
    else:
        df_chart["district_label"] = df_chart["district_name"].astype(str)

    fig = px.pie(
        df_chart,
        names="district_label",
        values="total_budget_model",
        hole=0.55,
        title="สัดส่วนงบประมาณของทุกแขวง",
        hover_data=[c for c in ["dept3", "division_name", "district_name"] if c in df_chart.columns],
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "งบประมาณ: %{value:,.0f} บาท<br>"
            "สัดส่วน: %{percent}<extra></extra>"
        ),
    )
    fig.update_layout(
        height=720,
        showlegend=True,
        legend_title_text="แขวง",
        margin=dict(t=80, b=40, l=40, r=40),
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("ดู Top 20 แขวงที่ได้งบสูงสุด"):
        top20 = df_chart.head(20).copy()
        top20["budget_share_percent"] = top20["total_budget_model"] / total_budget_all * 100
        show_cols = [c for c in ["dept3", "division_name", "district_name", "total_budget_model", "budget_share_percent"] if c in top20.columns]
        st.dataframe(
            top20[show_cols].style.format({
                "total_budget_model": "{:,.0f}",
                "budget_share_percent": "{:,.2f}%",
            }),
            use_container_width=True,
            height=420,
        )


@st.cache_data(show_spinner="กำลังอ่านไฟล์ Excel จาก folder data...")
def load_all(data_dir: str, cache_buster: int = 1):
    return build_master(data_dir)


@st.cache_data(show_spinner="กำลังคำนวณ baseline...")
def compute_baseline(
    master: pd.DataFrame,
    data_dir: str,
    max_factor_uplift: float,
    use_damage_probability: bool,
    workload_overrides: dict,
    budget_multiplier: float,
):
    return build_results(
        master,
        data_dir=data_dir,
        max_factor_uplift=max_factor_uplift,
        use_damage_probability=use_damage_probability,
        workload_overrides=workload_overrides,
        budget_multiplier=budget_multiplier,
    )


@st.cache_data(show_spinner=False)
def build_workload_parameter_table(data_dir: str):
    lookup = damage_lookup(data_dir)
    rows = []
    for cfg in WORKLOAD_CONFIG:
        p, unit_cost = get_dynamic_unit_cost_and_probability(cfg, lookup, data_dir=data_dir)
        rows.append(
            {
                "workload_item": cfg.get("item", ""),
                "category": cfg.get("category", ""),
                "quantity_col": cfg.get("quantity_col", ""),
                "unit": cfg.get("unit", ""),
                "damage_probability": float(p),
                "unit_cost": float(unit_cost),
                "apply_damage_probability": bool(cfg.get("apply_damage_probability", True)),
            }
        )
    return pd.DataFrame(rows)


@st.cache_data(show_spinner="กำลังคำนวณ unit cost ผิวจราจรจาก RMMS...")
def load_pavement_cost(data_dir: str):
    return build_pavement_unit_cost_from_rmms(data_dir)


# =========================================================
# Page header
# =========================================================

st.title("🛣️ Workload Cost Calculation Web App - test update")
st.caption(
    "Mockup สำหรับเลือกแขวง ปรับ quantity ได้ทุกรายการ และเห็นงบประมาณเปลี่ยนตามสูตรแบบ real-time "
    "โดยยังไม่ใช้ Cap Limit 6,000 ล้านบาท"
)


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:
    st.header("ตั้งค่า")
    data_dir = st.text_input("Data folder", value="data")
    damage_mode = st.selectbox(
        "Use Damage Probability",
        options=["On", "Off"],
        index=0,
    )
    use_damage_probability = damage_mode == "On"
    max_factor_uplift = st.slider(
        "Max Factor Uplift",
        min_value=0.0,
        max_value=0.50,
        value=float(MAX_FACTOR_UPLIFT),
        step=0.01,
        help="Max Factor Uplift คือ เพดานสูงสุดของการเพิ่มงบประมาณที่คำนวณจากปัจจัยแวดล้อม เช่น ปริมาณจราจร สภาพพื้นที่ ฯลฯ โดยจะนำไปคูณกับ Base Cost เพื่อเพิ่มงบให้สอดคล้องกับความยากง่ายของพื้นที่"
    )
    st.markdown("**Workload Parameter Grid**")
    param_df = build_workload_parameter_table(data_dir)
    editable_param_df = st.data_editor(
        param_df,
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "workload_item": st.column_config.TextColumn("Workload Item", disabled=True),
            "category": st.column_config.TextColumn("Category", disabled=True),
            "quantity_col": st.column_config.TextColumn("Quantity Column", disabled=True),
            "unit": st.column_config.TextColumn("Unit", disabled=True),
            "damage_probability": st.column_config.NumberColumn("Damage Probability", min_value=0.0, step=0.000001),
            "unit_cost": st.column_config.NumberColumn("Unit Cost", min_value=0.0, step=1.0),
            "apply_damage_probability": st.column_config.CheckboxColumn("Apply Damage Probability"),
        },
        key="workload_param_grid",
    )

    workload_overrides = {}
    for _, row in editable_param_df.iterrows():
        q_col = str(row.get("quantity_col", "")).strip()
        if not q_col:
            continue
        workload_overrides[q_col] = {
            "damage_probability": float(pd.to_numeric(row.get("damage_probability", 1.0), errors="coerce")),
            "unit_cost": float(pd.to_numeric(row.get("unit_cost", 0.0), errors="coerce")),
            "apply_damage_probability": bool(row.get("apply_damage_probability", True)),
        }

    # Find min non-zero unit cost for budget multiplier
    non_zero_costs = [float(row.get("unit_cost", 0)) for _, row in editable_param_df.iterrows() if float(row.get("unit_cost", 0)) > 0]
    default_x = min(non_zero_costs) if non_zero_costs else 100.0

    budget_multiplier = st.sidebar.number_input(
        "Budget Multiplier (X)",
        min_value=0.0,
        value=float(default_x),
        step=1.0,
        help="ตัวคูณสำหรับแปลงคะแนน Workload Unit เป็นงบประมาณ (บาท)"
    )

    st.divider()
    st.markdown("**สูตรหลัก**")
    st.code(
        """
Asset workload:
quantity × damage_probability × unit_cost

Pavement workload:
length_to2 × pavement_unit_cost

Total Budget:
Σ(workload) + factor + fixed_cost
""".strip()
    )
    st.caption("Version นี้ยังไม่ตัดงบด้วย cap limit และผิวจราจรไม่คูณ probability")


# =========================================================
# Load + baseline
# =========================================================

try:
    master = load_all(data_dir, cache_buster=4)
except Exception as e:
    st.error(str(e))
    st.stop()

baseline_summary, baseline_detail, baseline_master = compute_baseline(
    master,
    data_dir,
    max_factor_uplift,
    use_damage_probability,
    workload_overrides,
    budget_multiplier,
)


# =========================================================
# District selector
# =========================================================

master_view = baseline_master.copy()
master_view["district_label"] = master_view["dept3"].astype(str) + " - " + master_view["district_name"].astype(str)
master_view = master_view.sort_values(["division_name", "district_name"])

selected_label = st.sidebar.selectbox("1) เลือกแขวง", master_view["district_label"].tolist())
selected_dept3 = int(str(selected_label).split(" - ")[0])
selected_row = baseline_master.loc[baseline_master["dept3"].astype(int).eq(selected_dept3)].iloc[0]
st.sidebar.success(f"เลือกแล้ว: {selected_label}")


# =========================================================
# Quantity inputs
# =========================================================

st.subheader("2) ปรับ Quantity ของ Workload")
st.write(
    "ระบบตั้งค่า default จากข้อมูลเดิมของแขวงที่เลือกไว้ก่อน จากนั้น user สามารถแก้ quantity ได้ทุกรายการ "
    "เพื่อดูงบประมาณใหม่ทันที"
)

revised_master = baseline_master.copy()
mask = revised_master["dept3"].astype(int).eq(selected_dept3)

quantity_records = []
configs_by_category = {}
for idx, cfg in enumerate(WORKLOAD_CONFIG):
    configs_by_category.setdefault(cfg.get("category", "Other"), []).append((idx, cfg))

for category, cfgs in configs_by_category.items():
    with st.expander(f"{category} ({len(cfgs)} รายการ)", expanded=True):
        cols = st.columns(3)
        for j, (idx, cfg) in enumerate(cfgs):
            q_col = cfg["quantity_col"]
            default_value = float(pd.to_numeric(pd.Series([selected_row.get(q_col, 0)]), errors="coerce").fillna(0).iloc[0])
            label = f"{cfg['item']} ({cfg.get('unit', '')})"
            help_text = f"source column: {q_col}\n\n{cfg.get('note', '')}"
            step = 0.001 if cfg.get("unit") in ["กม.", "เมตร"] else 1.0
            fmt = "%.3f" if step < 1 else "%.0f"
            with cols[j % 3]:
                value = st.number_input(
                    label,
                    min_value=0.0,
                    value=default_value,
                    step=step,
                    format=fmt,
                    key=f"q_{idx}_{q_col}",
                    help=help_text,
                )
                if q_col == "length_to2":
                    warranty_val = float(pd.to_numeric(pd.Series([selected_row.get("warranty_distance", 0)]), errors="coerce").fillna(0).iloc[0])
                    st.text_input(
                        "ระยะติดค้ำประกัน (กม.)", 
                        value=f"{warranty_val:,.3f}", 
                        disabled=True, 
                        help="ระยะทางที่ยังอยู่ในช่วงรับประกัน ซึ่งระบบได้ทำการหักลบออกจากปริมาณงานตั้งต้นให้แล้ว"
                    )
            revised_master.loc[mask, q_col] = value
            quantity_records.append(
                {
                    "workload_item": cfg["item"],
                    "category": category,
                    "quantity_col": q_col,
                    "unit": cfg.get("unit", ""),
                    "default_quantity": default_value,
                    "revised_quantity": value,
                    "change": value - default_value,
                    "damage_key": cfg.get("damage_key"),
                    "unit_cost_config": cfg.get("unit_cost", 0),
                    "apply_damage_probability": cfg.get("apply_damage_probability", True),
                    "condition_profile": cfg.get("condition_profile", "none"),
                    "note": cfg.get("note", ""),
                }
            )

quantity_change_df = pd.DataFrame(quantity_records)


# =========================================================
# Recalculate after input
# =========================================================

revised_summary, revised_detail, revised_master_scored = build_results(
    revised_master,
    data_dir=data_dir,
    max_factor_uplift=max_factor_uplift,
    use_damage_probability=use_damage_probability,
    workload_overrides=workload_overrides,
    budget_multiplier=budget_multiplier,
)

base_one = baseline_summary.loc[baseline_summary["dept3"].astype(int).eq(selected_dept3)].iloc[0]
revised_one = revised_summary.loc[revised_summary["dept3"].astype(int).eq(selected_dept3)].iloc[0]


# =========================================================
# Result metrics
# =========================================================

st.divider()
st.subheader("3) ผลคำนวณงบประมาณ")

k1, k2, k3, k4 = st.columns(4)
k1.metric("Baseline total budget", baht(base_one["total_budget_model"]))
k2.metric(
    "Revised total budget",
    baht(revised_one["total_budget_model"]),
    delta=baht(revised_one["total_budget_model"] - base_one["total_budget_model"]),
)
k3.metric("National baseline", baht(float(baseline_summary["total_budget_model"].sum())))
k4.metric("National revised", baht(float(revised_summary["total_budget_model"].sum())))

chart_df = pd.DataFrame({
    "scenario": ["Baseline", "Revised"],
    "budget": [base_one["total_budget_model"], revised_one["total_budget_model"]],
})
fig = px.bar(chart_df, x="scenario", y="budget", text="budget", title="เปรียบเทียบงบประมาณของแขวงที่เลือก")
fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
fig.update_layout(yaxis_title="บาท", xaxis_title="")
st.plotly_chart(fig, use_container_width=True)


# =========================================================
# Line chart all districts
# =========================================================

st.subheader("กราฟเส้นงบประมาณรวมทุกแขวง")
line_base = baseline_summary[["dept3", "district_name", "total_budget_model"]].copy()
line_base = line_base.rename(columns={"total_budget_model": "baseline_budget"})
line_revised = revised_summary[["dept3", "district_name", "total_budget_model"]].copy()
line_revised = line_revised.rename(columns={"total_budget_model": "revised_budget"})
line_all = line_base.merge(line_revised, on=["dept3", "district_name"], how="inner")
line_all["district_label"] = line_all["dept3"].astype(str) + " - " + line_all["district_name"].astype(str)
line_all = line_all.sort_values("revised_budget", ascending=False)

line_plot = pd.concat(
    [
        line_all[["district_label", "baseline_budget"]].rename(columns={"baseline_budget": "budget"}).assign(scenario="Baseline"),
        line_all[["district_label", "revised_budget"]].rename(columns={"revised_budget": "budget"}).assign(scenario="Revised"),
    ],
    ignore_index=True,
)
fig_line = px.line(
    line_plot,
    x="district_label",
    y="budget",
    color="scenario",
    markers=True,
    title="เปรียบเทียบงบประมาณทุกแขวง (Baseline vs Revised)",
)
fig_line.update_layout(
    xaxis_title="District Name (แขวง)",
    yaxis_title="บาท",
    xaxis=dict(tickangle=90),
    legend_title_text="Scenario",
    height=560,
)
st.plotly_chart(fig_line, use_container_width=True)

# =========================================================
# Donut chart all districts
# =========================================================

st.divider()
show_budget_donut_chart(revised_summary)


# =========================================================
# Pavement unit cost audit
# =========================================================

st.divider()
st.subheader("ตรวจสอบ Unit Cost ผิวจราจร / ระยะทาง 2 ช่องจราจร")

try:
    pavement_cost = load_pavement_cost(data_dir)
    length_to2 = float(revised_master.loc[mask, "length_to2"].iloc[0]) if "length_to2" in revised_master.columns else 0.0
    #pavement_unit_cost = float(pavement_cost["pavement_unit_cost"])
    pavement_unit_cost = 60000  # ใช้ค่า unit cost แบบไม่คูณ probability เพื่อให้เห็นงบประมาณที่ลงไปจริงๆ ตามสูตรที่ใช้ใน model
    pavement_probability = float(pavement_cost["pavement_damage_probability"])

    c1, c2, c3 = st.columns(3)
    c1.metric("Pavement Unit Cost จาก RMMS ปี 2568", baht(pavement_unit_cost))
    c2.metric("Weighted Damage Probability", f"{pavement_probability:.6f}")
    c3.metric("สูตรที่ใช้จริง", "ไม่คูณ probability")

    with st.expander("เปรียบเทียบสูตรผิวจราจร: คูณ vs ไม่คูณโอกาสเกิดความเสียหาย", expanded=True):
        compare_pavement = pd.DataFrame([
            {
                "formula": "เดิม: length_to2 × probability × unit_cost",
                "length_to2": length_to2,
                "probability": pavement_probability,
                "unit_cost": pavement_unit_cost,
                "estimated_cost": length_to2 * pavement_probability * pavement_unit_cost,
            },
            {
                "formula": "ใช้จริง: length_to2 × unit_cost",
                "length_to2": length_to2,
                "probability": None,
                "unit_cost": pavement_unit_cost,
                "estimated_cost": length_to2 * pavement_unit_cost,
            },
        ])
        st.dataframe(
            compare_pavement.style.format({
                "length_to2": "{:,.3f}",
                "probability": "{:.6f}",
                "unit_cost": "{:,.2f}",
                "estimated_cost": "{:,.0f}",
            }),
            use_container_width=True,
        )

    with st.expander("ดูรายการ workcode ที่นำมารวมเป็น pavement unit cost"):
        pavement_detail = pavement_cost["detail"].copy()
        show_cols = [
            "surface_type",
            "workcode",
            "workname",
            "damage_probability",
            "rmms_quantity",
            "rmms_total_budget",
            "rmms_unit_cost",
        ]
        show_cols = [c for c in show_cols if c in pavement_detail.columns]
        st.dataframe(
            pavement_detail[show_cols].style.format({
                "damage_probability": "{:.6f}",
                "rmms_quantity": "{:,.2f}",
                "rmms_total_budget": "{:,.0f}",
                "rmms_unit_cost": "{:,.2f}",
            }),
            use_container_width=True,
            height=420,
        )
except Exception as e:
    st.warning(f"ไม่สามารถแสดงรายละเอียด pavement unit cost ได้: {e}")


# =========================================================
# Breakdown
# =========================================================

st.divider()
st.subheader("4) Breakdown ของสูตร")
breakdown = pd.DataFrame([
    {"component": "Base Workload", "baseline": base_one["base_workload_cost"], "revised": revised_one["base_workload_cost"]},
    {"component": "Factor", "baseline": base_one["factor_cost"], "revised": revised_one["factor_cost"]},
    {"component": "Fixed Cost: ค่าเช่าเครื่องจักร", "baseline": base_one["machine_rental_cost"], "revised": revised_one["machine_rental_cost"]},
    {"component": "Fixed Cost: งานตัดหญ้า", "baseline": base_one["grass_cost_estimate"], "revised": revised_one["grass_cost_estimate"]},
    {"component": "Total Budget", "baseline": base_one["total_budget_model"], "revised": revised_one["total_budget_model"]},
])
breakdown["change"] = breakdown["revised"] - breakdown["baseline"]
st.dataframe(
    breakdown.style.format({"baseline": "{:,.0f}", "revised": "{:,.0f}", "change": "{:,.0f}"}),
    use_container_width=True,
)


# =========================================================
# Quantity change table
# =========================================================

st.subheader("5) Quantity ที่ user ปรับ")
st.dataframe(
    quantity_change_df.style.format({
        "default_quantity": "{:,.3f}",
        "revised_quantity": "{:,.3f}",
        "change": "{:,.3f}",
        "unit_cost_config": "{:,.0f}",
    }),
    use_container_width=True,
    height=360,
)


# =========================================================
# Workload detail
# =========================================================

st.subheader("6) Workload Detail รายการคำนวณ")
selected_detail = revised_detail.loc[revised_detail["dept3"].astype(int).eq(selected_dept3)].copy()
selected_detail_cols = [
    "workload_item",
    "category",
    "quantity",
    "unit",
    "damage_probability",
    "unit_cost",
    "apply_damage_probability",
    "base_value",
    "total_quantity",
    "workload_unit",
    "workload_score",
    "base_workload_cost",
    "condition_profile",
    "factor_index_0_1",
    "factor_cost",
    "workload_plus_factor",
    "note",
]
selected_detail_cols = [c for c in selected_detail_cols if c in selected_detail.columns]
st.dataframe(
    selected_detail[selected_detail_cols].style.format({
        "quantity": "{:,.3f}",
        "damage_probability": "{:.6f}",
        "unit_cost": "{:,.0f}",
        "base_value": "{:.4f}",
        "total_quantity": "{:,.3f}",
        "workload_unit": "{:,.6f}",
        "workload_score": "{:,.6f}",
        "base_workload_cost": "{:,.0f}",
        "factor_index_0_1": "{:.4f}",
        "factor_cost": "{:,.0f}",
        "workload_plus_factor": "{:,.0f}",
    }),
    use_container_width=True,
    height=430,
)


# =========================================================
# Summary all districts
# =========================================================

st.subheader("7) Summary ทุกแขวง")
st.caption("Version นี้แสดงงบจริงจากสูตร model โดยยังไม่มีการ scale/cap งบประมาณ")
summary_view = revised_summary.sort_values("total_budget_model", ascending=False)[[
    "dept3",
    "division_name",
    "district_name",
    "base_workload_cost",
    "factor_cost",
    "fixed_cost",
    "total_budget_model",
]]
st.dataframe(
    summary_view.style.format({
        "base_workload_cost": "{:,.0f}",
        "factor_cost": "{:,.0f}",
        "fixed_cost": "{:,.0f}",
        "total_budget_model": "{:,.0f}",
    }),
    use_container_width=True,
    height=380,
)


# =========================================================
# Download
# =========================================================

csv = revised_summary.to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "Download revised summary CSV",
    data=csv,
    file_name="revised_workload_cost_summary_no_cap.csv",
    mime="text/csv",
)


# =========================================================
# Debug
# =========================================================

with st.expander("ดูค่าตั้งต้นและ score ของแขวงที่เลือก"):
    cols = [
        "dept3",
        "division_name",
        "district_name",
        "length_to2",
        "Cluster",
        "traffic_score",
        "truck_score",
        "elevation_score",
        "rain_score",
        "operating_distance",
        "operating_distance_score",
        "machine_rental_cost",
    ]
    cols = [c for c in cols if c in revised_master_scored.columns]
    st.dataframe(
        revised_master_scored.loc[revised_master_scored["dept3"].astype(int).eq(selected_dept3), cols],
        use_container_width=True,
    )

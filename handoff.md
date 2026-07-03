# Project Handoff: RMMS Workload Web Application

This document summarizes the current state, configuration, and recent changes in this workspace to help any new session or AI agent pick up the task seamlessly.

## Workspace Overview

- **Project Path**: `C:\Users\Sunday\.gemini\antigravity\scratch\RMMS_workload_webapp`
- **Active Git Branch**: `streamlit` (tracking `origin/streamlit`)
- **Git Executable**: `C:\Program Files\Git\bin\git.exe`
- **Local Git Identity Configured**:
  - **Name**: `ibe-infraplus`
  - **Email**: `ibe.infraplus@gmail.com`

## Branches

- **`main`**: React (frontend) + FastAPI (backend) production-ready stack.
- **`streamlit`**: Streamlit single-file dashboard implementation (`app.py`), used for quick deployments (e.g. on Streamlit Community Cloud).

## Latest Actions & Changes

### 1. Workload Unit & Score Formula Implementation (Option 2 - 2026-07-02)
Implemented a relative scoring mathematical model for all workload items:
- **Base Value (i)**:
  $$\text{Base Value}_i = \frac{\text{Unit Cost}_i}{\text{Min Unit Cost}}$$
  (where `Min_Unit_Cost` is the lowest non-zero Unit Cost).
- **Workload Unit (i)**:
  $$\text{Workload Unit}_i = \text{Base Value}_i \times \text{Quantity}_{\text{district}, i}$$
- **Workload Score (i)**:
  $$\text{Workload Score}_i = \text{Workload Unit}_i \times \text{Damage Probability}_i$$
- **Workload Cost (i)**:
  $$\text{Workload Cost}_i = \text{Workload Score}_i \times X$$
  (where $X$ is a configurable Budget Multiplier, defaulting to `Min_Unit_Cost`).

Code updates:
- Updated [src/calculator.py](file:///C:/Users/Sunday/.gemini/antigravity/scratch/RMMS_workload_webapp/src/calculator.py) to process new workload unit equations.
- Modified [main.py](file:///C:/Users/Sunday/.gemini/antigravity/scratch/RMMS_workload_webapp/main.py) to add `budget_multiplier` parameter to API request schemas.
- Modified [app.py](file:///C:/Users/Sunday/.gemini/antigravity/scratch/RMMS_workload_webapp/app.py) to restructure the dashboard:
  - **Section 3**: Displays Workload Unit and Workload Score results, and embeds the **Budget Multiplier (X)** input widget.
  - **Section 4**: Displays simulated Budget Cost results (Baht), bar charts, line charts, and donut charts.
  - Remaining sections are incremented (Section 5: Breakdown, Section 6: Quantity updates, Section 7: Workload detail, Section 8: Summary of all districts).
  - Also added module hot-reload statements.
- Modified [App.jsx](file:///C:/Users/Sunday/.gemini/antigravity/scratch/RMMS_workload_webapp/frontend/src/App.jsx) to add input fields and columns for the React frontend counterpart.

### 2. Policy Workload Removal (Implemented - 2026-07-02)
- Removed "Policy" workload category ("งานนโยบาย") and its three items:
  1. `ค่าบำรุงจุดกางเต็นท์`
  2. `ค่าบำรุงจุดพักรถ`
  3. `ค่าบำรุงภูมิสถาปัตย์`
- Cleaned up config and layouts:
  - Removed `rain_only` profile from `FACTOR_PROFILES` in `src/config.py`.
  - Updated formula labels from "Asset / Policy workload" to "Asset workload" in `app.py` and `frontend/src/App.jsx`.

---

## How to Resume Work

1. **Running locally**:
   - Install dependencies: `pip install -r requirements.txt`
   - Run the Streamlit app: `streamlit run app.py`

2. **Next Steps**:
   - Verify the deployment updates successfully on the live Streamlit Community Cloud site.
   - Adjust the Budget Multiplier (X) in the sidebar to simulate budgets.

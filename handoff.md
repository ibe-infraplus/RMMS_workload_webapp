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

### 1. Warranty Distance & Live API Updates (Pulled from upstream - 2026-07-02)
- Added live DOH API lookup for years 2567, 2568, and 2569 action plans to retrieve warranty distance.
- Subtracted warranty distance from `length_to2` (pavement length) in the workload data loader.
- Added 24-hour API response cache (`api_warranty_cache.json`).
- Updated Streamlit UI to show a read-only "ระยะติดค้ำประกัน (กม.)" input description below the pavement length.

### 2. Policy Workload Removal (Implemented - 2026-07-02)
- Removed "Policy" workload category ("งานนโยบาย") and its three items:
  1. `ค่าบำรุงจุดกางเต็นท์` (จำนวนจุดกางเต็นท์)
  2. `ค่าบำรุงจุดพักรถ` (จำนวนจุดพักรถ)
  3. `ค่าบำรุงภูมิสถาปัตย์` (จำนวนภูมิสถาปัตย์)
- Cleaned up config and layouts:
  - Removed `rain_only` profile from `FACTOR_PROFILES` in `src/config.py`.
  - Updated formula labels from "Asset / Policy workload" to "Asset workload" in `app.py` and `frontend/src/App.jsx`.
  - Removed "Policy" from category lists in `frontend/src/App.jsx` parameter modal.
- Committed and pushed changes successfully to `origin/streamlit`.

## How to Resume Work

1. **Running locally**:
   - Install dependencies: `pip install -r requirements.txt`
   - Run the Streamlit app: `streamlit run app.py`

2. **Next Steps**:
   - Verify the deployment updates successfully on the live Streamlit Community Cloud site.
   - Verify that "งานนโยบาย" (Policy) items no longer show in the parameters or calculations.

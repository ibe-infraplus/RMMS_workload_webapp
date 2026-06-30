---
name: rmms-workload-helper
description: Guidelines and instructions for working on the RMMS Workload Web Application (FastAPI/React and Streamlit versions)
---

# RMMS Workload Webapp Development Guide

Use this skill when the user asks you to modify, run, debug, or deployment-check the RMMS Workload Web Application.

## Key Configurations

- **Project Location**: `C:\Users\Sunday\.gemini\antigravity\scratch\RMMS_workload_webapp`
- **Git Path**: Always run git using `C:\Program Files\Git\bin\git.exe` in this environment.
- **Git User Config**:
  - Name: `ibe-infraplus`
  - Email: `ibe.infraplus@gmail.com`

## Branch Architecture

1. **`main` Branch**:
   - Modern webapp built with **Vite, React, and Vanilla CSS** on the frontend, and **FastAPI (Python) + Uvicorn** on the backend.
   - Run backend: `python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload`
   - Run frontend: Navigate to `frontend/`, run `npm install` and then `npm run dev`.

2. **`streamlit` Branch**:
   - Streamlit single-page application dashboard (`app.py`).
   - Run app: `streamlit run app.py`
   - Linked to live deployment (e.g., Streamlit Community Cloud) where any push to `origin/streamlit` automatically redeploys.

## Guidelines for Modifying Code

- **Always check the active branch**: Run `git branch` before editing to know if you're editing `app.py` (streamlit branch) or the FastAPI/React files (main branch).
- **Verify calculation logic**: Core logic resides in `src/calculator.py`, `src/config.py`, and `src/data_loader.py`. Make sure any updates to the math are consistent across both frontend architectures.
- **Pushing changes**: Since Git credentials are cached on the machine, you can run `git push origin <branch>` directly after staging and committing.

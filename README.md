# RMMS Workload Web Application

Welcome to the RMMS Workload Web Application repository. 

This project is designed to calculate and simulate workload costs dynamically. It supports **two different frontend interfaces** to match your deployment needs:

## 1. Modern Web App (React + FastAPI) 🌟
This is the recommended, production-ready version. It separates the backend logic from the frontend UI for maximum performance and stability, allowing for self-deployment via Docker.

- **Frontend**: Built with Vite, React, and Vanilla CSS (Glassmorphism design).
- **Backend**: Built with FastAPI (Python) and Uvicorn.
- **Features**: Real-time budget simulation, dynamic parameter grid (add/delete/categorize parameters), interactive Plotly charts, and responsive design.
- **Deployment**: Fully dockerized.

**How to run (Docker):**
```bash
docker-compose up -d --build
```
> See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed Docker instructions.

**How to run locally (Without Docker):**
You can use the provided `run.bat` script on Windows to start both the FastAPI server and Vite frontend simultaneously.

---

## 2. Legacy App (Streamlit)
The original Streamlit application is still available in the repository (`app.py`). It is a monolithic architecture that runs both the frontend and backend in a single Python process.

- **Features**: Streamlit sidebar inputs, data editor grids, Plotly charts.
- **Deployment**: Can be deployed on Streamlit Community Cloud or run locally.

**How to run:**
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Data Management
Both systems share the same underlying logic (`src/`) and data source (`data/`). 
Any updates to the Excel files inside the `data/` folder will be reflected in both the React app and the Streamlit app automatically.

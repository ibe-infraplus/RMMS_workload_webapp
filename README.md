# RMMS Workload Web Application

Welcome to the RMMS Workload Web Application repository. 

This project is designed to calculate and simulate workload costs dynamically using a Modern Web App architecture.

## 1. Modern Web App (React + FastAPI) 🌟
This is the production-ready version. It separates the backend logic from the frontend UI for maximum performance and stability, allowing for self-deployment via Docker.

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

To run the application manually, you need to start both the FastAPI backend and the React frontend in separate terminal windows.

**Terminal 1: Start the Backend**
```bash
# From the root directory (where main.py is)
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**Terminal 2: Start the Frontend**
```bash
# Navigate to the frontend directory
cd frontend
npm install
npm run dev
```
Then, open your browser to `http://localhost:5173` to access the application.

## Contents


```text
Pavement workload = length_to2 × pavement_unit_cost
```

โดย **ไม่คูณ damage probability** กับผิวจราจรแล้ว

- `pavement_unit_cost` คำนวณจาก:
  - รหัสงานใน section `ค่ามาตรฐานการซ่อมบำรุงถนนอ้างอิง` จากไฟล์ `ข้อมูลโอกาสเกิดความเสียหาย (1).xlsx`
  - unit cost จากไฟล์ `แผนงาน RMMS.xlsx` เฉพาะปี 2568
- เพิ่ม donut chart สำหรับดูสัดส่วนงบประมาณที่ลงไปในแต่ละแขวง
- เพิ่มตาราง audit เพื่อตรวจสอบ workcode ที่นำมารวมเป็น pavement unit cost
- เพิ่ม comparison สูตรผิวจราจรแบบ `คูณ probability` และ `ไม่คูณ probability`

## Project structure

```text
workload_webapp/
├─ requirements.txt
├─ README.md
├─ data/
│  ├─ ข้อมูลโอกาสเกิดความเสียหาย (1).xlsx
│  ├─ แผนงาน RMMS.xlsx
│  ├─ cluster_district.xlsx
│  └─ group_data_final.xlsx
│  └─ operating_distances.xlsx
└─ src/
   ├─ __init__.py
   ├─ config.py
   ├─ data_loader.py
   └─ calculator.py
```

## วิธีรันบน VS Code

**How to run (Docker):**
```bash
docker-compose up -d --build
```
> See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed Docker instructions.

**How to run locally (Without Docker):**
You can use the provided `run.bat` script on Windows to start both the FastAPI server and Vite frontend simultaneously.


- **Warranty Distance (?????????????)**: ?????????????? esponse*.json (???? response2567.json) ????????????????? data/ ????? distance ??????????????????????????? ?????????????????? length_to2 ???????????? ????????? ??????????????????????????????????????????????????????????????????????????? (??????????????????????????? 0)

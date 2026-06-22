# Workload Cost Calculation Web App

Streamlit mockup สำหรับ demonstrate การคำนวณงบประมาณงานบำรุงปกติของกรมทางหลวง

## สิ่งที่อัปเดตในเวอร์ชันนี้

- User เลือกแขวงและปรับ quantity ได้ทุกรายการ
- ยังไม่ใช้ cap limit 6,000 ล้านบาท
- `ระยะทาง 2 ช่องจราจร` ใช้สูตรใหม่:

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
├─ app.py
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

```bash
cd workload_webapp
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

ถ้าใช้ PowerShell แล้ว activate ไม่ได้ ให้รัน:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.venv\Scripts\Activate.ps1
```

## สูตรหลัก

```text
Asset / Policy workload:
quantity × damage_probability × unit_cost

Pavement workload:
length_to2 × pavement_unit_cost

Total Budget:
Σ(workload) + factor + fixed_cost
```

# 🚀 คู่มือการทดสอบ API สำหรับ Developer

หลังจากที่มีการปรับโครงสร้าง Backend ให้กลายเป็น **Granular API** ที่สามารถดึงข้อมูลย่อยๆ และยิงทดสอบแบบรายแขวงได้แล้ว คู่มือนี้จะช่วยให้ทีม Frontend หรือ Developer สามารถใช้เครื่องมือเช่น `cURL`, `Postman`, หรือ Swagger UI เพื่อทดสอบ Endpoint ต่างๆ ได้อย่างง่ายดาย

---

## 🛠️ 1. การใช้งาน Swagger UI (ง่ายที่สุด)
FastAPI มีหน้าเว็บสำหรับทดสอบ API แบบ Interactive ในตัว (ไม่ต้องลงโปรแกรมเพิ่ม)
1. รันเซิร์ฟเวอร์ด้วยคำสั่ง: `python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload`
2. เปิดเบราว์เซอร์ไปที่: **`http://localhost:8001/docs`**
3. คุณจะเห็นรายชื่อ API ทั้งหมด ให้กดปุ่ม **"Try it out"** ที่ API เส้นที่ต้องการ กรอก Parameter แล้วกด **"Execute"** เพื่อดูผลลัพธ์ JSON ได้เลย

---

## 💻 2. ทดสอบด้วย cURL (Command Line)
หากต้องการทดสอบผ่าน Command Line สามารถยิงคำสั่งเหล่านี้ได้เลย (ตัวอย่างพอร์ต 8001):

### 📌 2.1 ดึงรายชื่อแขวงทั้งหมด
เส้นนี้ใช้สำหรับทำ Dropdown เลือกแขวงในหน้า Frontend
```bash
curl -X 'GET' 'http://localhost:8001/api/districts' -H 'accept: application/json'
```
**ตัวอย่าง Response:**
```json
{
  "districts": [
    {
      "dept3": 100,
      "district_label": "100 - แขวงทางหลวงสมุทรปราการ",
      "division_name": "สทล.13 (กรุงเทพ)",
      "district_name": "สมุทรปราการ"
    }
  ]
}
```

### 📌 2.2 ดึงข้อมูลดิบ (Raw Quantities) ของแขวง 
เส้นนี้ใช้เพื่อพรีโหลดค่าตั้งต้น (เช่น ระยะทาง, ปริมาณงานเริ่มต้น) ของแขวงนั้นๆ มาแสดงบนฟอร์ม
*(ตัวอย่าง: ดึงข้อมูลของรหัสแขวง 100)*
```bash
curl -X 'GET' 'http://localhost:8001/api/districts/100' -H 'accept: application/json'
```

### 📌 2.3 ดึงการตั้งค่า Parameter Grid
เส้นนี้ใช้สำหรับดึงเรทตั้งต้น เช่น Damage Probability และ Unit Cost เพื่อแสดงในตารางให้ User ปรับแก้
```bash
curl -X 'GET' 'http://localhost:8001/api/config' -H 'accept: application/json'
```

### 📌 2.4 ยิงทดสอบจำลองงบประมาณ (Calculate) ของแขวงแบบเจาะจง
เมื่อ User ปรับแก้ค่าต่างๆ ใน Grid หรือแก้ไขปริมาณงาน ระบบจะยิงข้อมูลกลับมาเส้นนี้ เพื่อคำนวณงบประมาณเฉพาะแขวงนั้นใหม่ (ลดโหลดการคำนวณทั้งประเทศ)
```bash
curl -X 'POST' \
  'http://localhost:8001/api/calculate/100' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "max_factor_uplift": 0.15,
  "use_damage_probability": true,
  "workload_overrides": {
    "asset_pavilion_num": {
      "damage_probability": 0.5,
      "unit_cost": 150000
    }
  },
  "quantity_updates": {
    "asset_pavilion_num": 10
  },
  "custom_config": null
}'
```
**สิ่งที่ส่งไป (`Body`):**
*   `max_factor_uplift`: เพดาน Factor (เช่น 0.15 คือ 15%)
*   `workload_overrides`: การแก้ตัวคูณหรือราคากลางรายไอเทม
*   `quantity_updates`: การแก้ตัวเลขปริมาณงาน (Quantity) ของแขวงนี้
*   `custom_config`: (Optional) โครงสร้าง Parameter Grid ใหม่ หากต้องการแก้โครงสร้างตาราง (ถ้าไม่ได้แก้ ให้ส่ง `null` หรือเอาตัวแปรนี้ออก)

**สิ่งที่จะได้รับ (`Response`):** 
จะคืนค่า `total_budget_model` (งบใหม่), `breakdown` (แจกแจง Base, Factor, Fixed cost), และ `workload_detail` (รายการย่อยทั้งหมดที่ถูกคำนวณแล้ว)

---

## 🚨 3. ปัญหาที่พบบ่อย (Troubleshooting)

**1. อาการ: ยิง API แล้วได้ `500 Internal Server Error`**
*   **สาเหตุหลัก:** มักเกิดจาก **ไฟล์ `master_final.xlsx` กำลังถูกเปิดค้างไว้ด้วยโปรแกรม Microsoft Excel** ทำให้ Python (Pandas) ไม่ได้รับอนุญาต (Permission Denied) ให้ไปอ่านไฟล์นั้น
*   **วิธีแก้:** ให้ปิดไฟล์ Excel นั้นก่อน แล้วลองยิง API ใหม่อีกครั้ง หรือเช็คว่ามี User อื่นล็อคไฟล์ไว้ใน Share Drive หรือไม่

**2. อาการ: ยิงแล้วได้ `404 Not Found`**
*   **วิธีแก้:** ตรวจสอบว่าพอร์ตที่รัน `uvicorn` ตรงกับใน URL หรือไม่ (บางเครื่องอาจเด้งไปพอร์ต 8001 ถ้า 8001 ไม่ว่าง) และให้เช็คว่ามี `/api/` นำหน้าเสมอ

**3. อาการ: ยิงแล้วได้ `422 Unprocessable Entity` (Validation Error)**
*   **สาเหตุหลัก:** มักเกิดจากการส่งข้อมูลผิด Data Type เช่น Swagger UI ดันใส่ค่าเริ่มต้น `custom_config: ["string"]` มาให้ ซึ่งระบบรับเป็นโครงสร้างแบบ JSON (Dictionary) เท่านั้น
*   **วิธีแก้:** ให้เปลี่ยน `custom_config` เป็น `null` หรือลบทิ้งออกจากกล่อง Request Body ไปเลยก่อนยิงทดสอบครับ

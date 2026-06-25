# 🔄 แนวทางการปรับเปลี่ยนระบบดึงข้อมูลเป็น API (API Integration Guide)

เอกสารฉบับนี้จัดทำขึ้นเพื่อเป็นแนวทางสำหรับนักพัฒนา (Developer) ในกรณีที่ต้องการย้ายระบบจากการอ่านข้อมูลผ่านไฟล์ Excel (File-based) ไปเป็นการเชื่อมต่อข้อมูลโดยตรงจาก API ของระบบอื่น (API-based Integration)

## 📌 1. ภาพรวมของสถาปัตยกรรม (Architecture Overview)
ระบบปัจจุบันถูกออกแบบโดยคำนึงถึงการปรับเปลี่ยนในอนาคต (Modularity) อยู่แล้ว โดยกระบวนการนำเข้าข้อมูลทั้งหมดจะถูกรวมศูนย์ไว้ที่ไฟล์ `src/data_loader.py` 

ฟังก์ชันต่างๆ เช่น `load_asset_quantities()`, `load_district_base()` หรือ `load_damage()` ทำหน้าที่เป็นเสมือน "ปลั๊กอิน (Adapter)" ที่คอยดึงข้อมูลจากแหล่งต่างๆ แล้วแปลงให้อยู่ในรูปของ `pandas.DataFrame` ก่อนส่งให้เครื่องคิดเลข (`calculator.py`) ทำงานต่อ

ดังนั้น การเปลี่ยนไปใช้ API **ไม่จำเป็นต้องแก้ไข Logic การคำนวณงบประมาณใดๆ ทั้งสิ้น** เพียงแค่แก้ไขวิธีการดึงข้อมูลภายในไฟล์ `data_loader.py` เท่านั้น

---

## 💻 2. ขั้นตอนการปรับเปลี่ยนโค้ด (Implementation Steps)

### Step 2.1: เปลี่ยนตัวดึงข้อมูล (Data Source)
ในไฟล์ `src/data_loader.py` ให้ทำการเปลี่ยนโค้ดส่วนที่อ่านไฟล์ Excel ด้วย `pd.read_excel()` ไปเป็นการเรียกใช้ HTTP Request (เช่น ใช้ไลบรารี `requests` หรือ `httpx`)

**ตัวอย่างระบบเดิม (อ่านจาก Excel):**
```python
def load_asset_quantities(data_dir=None):
    raw = pd.read_excel(file_path("group", data_dir), sheet_name="ASSET")
    df = pd.DataFrame(raw)
    # ... process mapping ...
```

**ตัวอย่างระบบใหม่ (ดึงจาก API ภายนอก):**
```python
import requests
import pandas as pd

def load_asset_quantities(data_dir=None):
    # ยิง API ไปยังระบบฐานข้อมูล Asset (ตัวอย่าง)
    response = requests.get("https://api.external-system.com/v1/assets/quantities")
    response.raise_for_status() # เช็ค Error 400, 500
    
    data = response.json()
    
    # แปลง JSON Array เป็น DataFrame
    df = pd.DataFrame(data)
    # ... process mapping ...
```

### Step 2.2: การแปลงชื่อฟิลด์ (Data Mapping)
ข้อมูล JSON ที่ตอบกลับมาจากระบบอื่น มักจะมีชื่อ Field ที่ต่างออกไปจากที่ระบบเราคาดหวัง เช่น ระบบอื่นอาจจะส่ง key มาชื่อ `pavilionCount` แต่ระบบ Workload ของเราคาดหวังคอลัมน์ชื่อ `asset_pavilion_num`

ให้ทำการเปลี่ยนชื่อคอลัมน์ (Rename) ใน DataFrame ให้ตรงกับมาตรฐานที่ระบุไว้ในคู่มือ **`DATA_MAPPING.md`** เสมอ

**ตัวอย่างการทำ Mapping:**
```python
    df = df.rename(
        columns={
            "deptCode": "dept3",
            "pavilionCount": "asset_pavilion_num",
            "trafficLightUnit": "asset_traffic_light_num"
        }
    )
    
    # สำคัญ: ต้องกรองให้เหลือเฉพาะคอลัมน์ที่ระบบเราต้องใช้ เพื่อลดการกิน Memory
    return df[["dept3", "asset_pavilion_num", "asset_traffic_light_num"]]
```

---

## ⚡ 3. ข้อควรระวังด้านประสิทธิภาพ (Performance & Caching)

การที่ระบบ Workload ยิง API ไปยังระบบอื่นแบบ Real-time ทุกครั้งที่มีการขอคำนวณงบประมาณ อาจทำให้เกิดปัญหาดังนี้:
1. **Latency:** รอ Network นาน ทำให้ API ของเราตอบสนอง (Response Time) ช้าลง
2. **Rate Limit / API ล่ม:** หากมี User เข้าใช้งานระบบ Workload พร้อมกันจำนวนมาก อาจทำให้ระบบต้นทางล่ม หรือโดนแบนจาก Rate Limit

### 💡 แนวทางแก้ไขที่แนะนำ (Best Practices)
ควรใช้หลักการ **Caching Strategy** มาช่วย:

**วิธีที่ 1: Scheduled Sync (แนะนำ)**
*   เขียนสคริปต์ (Cronjob หรือ Background Task) ให้ไปดึงข้อมูลจาก API ต้นทางวันละ 1-2 ครั้ง (เช่น ช่วงตี 2)
*   นำข้อมูลที่ดึงมา เซฟลง Database ของตัวเอง หรือเซฟลงไฟล์ `master_final.xlsx` 
*   ให้ API ระบบ Workload ทำงานโดยอ่านจาก Cache ตัวนี้แทนการวิ่งไปยิงระบบอื่นแบบสดๆ

**วิธีที่ 2: In-Memory Cache + TTL**
*   ใช้เครื่องมืออย่าง Redis หรือ Python `cachetools` (เช่น `@cached(TTLCache(maxsize=10, ttl=3600))`)
*   ดึงข้อมูลจาก API มาเก็บไว้ใน RAM เป็นเวลา 1 ชั่วโมง หากมี Request เข้ามาในชั่วโมงนั้นก็เอาของเก่าไปตอบทันที

---

## ✅ สรุป Checklist สำหรับ Developer
- [ ] ศึกษาคู่มือ `DATA_MAPPING.md` ว่าระบบต้องการคอลัมน์ชื่ออะไรบ้าง
- [ ] เปลี่ยนคำสั่ง `pd.read_excel()` เป็น `requests.get()` ใน `data_loader.py`
- [ ] เขียนโค้ดแปลง JSON Response เป็น DataFrame
- [ ] จัดการเปลี่ยนชื่อคอลัมน์ (.rename) ให้ตรงตามมาตรฐาน
- [ ] (Optional แต่ควรทำ) เพิ่มระบบ Cache เพื่อลดภาระของระบบต้นทาง

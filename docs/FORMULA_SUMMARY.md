# RMMS Workload Cost - Formula & Data Summary

เอกสารฉบับนี้เป็นคู่มือฉบับสมบูรณ์สำหรับ Developer เพื่อทำความเข้าใจที่มาของข้อมูลในไฟล์ **`master_final.xlsx`** และสูตรการคำนวณงบประมาณ (Workload Cost & Factor Cost) แบบ Step-by-Step ตั้งแต่การเตรียมข้อมูลไปจนถึงตัวเลขสุดท้ายที่แสดงผล

---

## 1. ที่มาของข้อมูลใน `master_final.xlsx` (Data Lineage)

ไฟล์ `master_final.xlsx` เป็น **Single Source of Truth** ที่มีข้อมูล 1 บรรทัดต่อ 1 แขวง (1 row per district) เกิดจากการรวมร่าง (Merge) ข้อมูลจาก 4 แหล่งหลักในอดีต ดังนี้:

### 1.1 ข้อมูลโครงสร้างและสถิติ (Base & Input Data)
**ดึงมาจากไฟล์ต้นทาง:** `group_data_final.xlsx` (ชีต `group_data_final` และ `input`)
*   **คอลัมน์โครงสร้าง:** `dept3` (รหัสแขวง 3 หลัก), `division_name` (ชื่อเขต/สังกัด), `district_name` (ชื่อแขวง)
*   **คอลัมน์สถิติพื้นฐาน (อิง Prefix `input_`):**
    *   `length_to2`: ระยะทางแบบ 2 ช่องจราจร (นำไปเป็นปริมาณงานกลุ่ม Pavement)
    *   `input_veh_total`: ปริมาณจราจร AADT รวม
    *   `input_avg_iri`: ค่าความเรียบของผิวทางเฉลี่ย
    *   `input_elevation_var` / `input_slope_mean` / `input_slope_var`: ค่าสถิติความลาดชันและความสูงชันของพื้นที่แขวง
    *   `พื้นที่ฝนชุก`: สถิติพื้นที่ฝนตกชุก (เช่น วันฝนตก)

### 1.2 ข้อมูลปริมาณงานสินทรัพย์ (Asset Quantities)
**ดึงมาจากไฟล์ต้นทาง:** `group_data_final.xlsx` (ชีต `ASSET`)
*   **คอลัมน์ปริมาณงาน:** ได้แก่ `asset_culvert_underpass_num` (ท่อลอดทาง), `asset_traffic_light_num` (ไฟสัญญาณจราจร), `asset_street_light_num` (ไฟฟ้าแสงสว่าง) เป็นต้น
*   **Logic:** ดึงตัวเลขจำนวนเต็มมาใส่ หากเป็นค่าว่างจะถูกแปลงเป็น `0`

### 1.3 ข้อมูลระยะทางดำเนินการ (Operating Distances)
**ดึงมาจากไฟล์ต้นทาง:** `operating_distances.xlsx`
*   **คอลัมน์:** `operating_distance` (กิโลเมตร) 
*   **Logic:** นำระยะทางของสายทางย่อยๆ มาหาผลรวม (Sum) รวมกันตามรหัสแขวง `dept3`

### 1.4 ข้อมูลราคากลางเดิม & ค่าเช่าเครื่องจักร (RMMS Budget)
**ดึงมาจากไฟล์ต้นทาง:** `แผนงาน RMMS.xlsx`
*   **คอลัมน์:** `machine_rental_cost` (ค่าเช่าเครื่องจักร), `rmms_total_budget` (งบรวมเดิม)
*   **Logic:** กรองเฉพาะแผนงานปีงบประมาณที่สนใจ (เช่น 2568) แล้ว Sum งบประมาณตามรหัสแขวง `dept3`


---

## 2. ขั้นตอนการคำนวณงบประมาณ (Formula Step-by-Step)

การคำนวณแบ่งออกเป็น 3 ส่วนหลัก: **Base Workload Cost**, **Factor Cost** (เงินปรับแก้ตามสภาพพื้นที่), และ **Fixed Cost** (ค่าเช่าเครื่องจักร/งานตัดหญ้า)

### Step 2.1: คำนวณ Base Workload Cost (งบฐาน)
คำนวณแยกตามรายการงาน (Workload Item) แต่ละรายการ เช่น ผิวทาง, ไฟฟ้าแสงสว่าง

**สูตรทั่วไป:**
```text
Base Cost = Quantity × Damage Probability × Unit Cost
```
*   **Quantity (ปริมาณงาน):** ดึงจากคอลัมน์ใน `master_final.xlsx` (อิงตามที่เซ็ตใน Parameter Grid)
*   **Damage Probability (ความน่าจะเป็นที่จะพัง):** โอกาสพังต่อปี ดึงจากไฟล์ `ข้อมูลโอกาสเกิดความเสียหาย (1).xlsx` (เป็นสัดส่วน 0 ถึง 1)
*   **Unit Cost (ราคากลางต่อหน่วย):** ดึงจากไฟล์ข้อมูล หรือเซ็ตเป็น Default ในโค้ด

**ข้อยกเว้นสำหรับผิวจราจร (Pavement):**
รายการผิวทางจะไม่ใช้ Damage Probability แบบตรงๆ แต่ใช้ "ค่าเฉลี่ยถ่วงน้ำหนัก (Weighted Average Probability)" ของงานซ่อมถนนทุกประเภทรวมกัน หารด้วยราคากลางมาตรฐาน 
*(เช่น ผลรวมน้ำหนัก = 96.846 / Unit Cost = 35,000 จะได้ค่า Probability = 0.002767)*

### Step 2.2: คำนวณ Factor Index (ดัชนีชี้วัดความยากในการทำงานของพื้นที่)
เพื่อนำไปปรับเพิ่มงบให้แขวงที่ทำงานยาก ระบบจะสร้าง **Condition Score** ออกมา 5 ด้าน โดยเทียบอันดับ (Percentile Ranking 0 ถึง 1) ระหว่างทุกแขวงในประเทศ:

1.  **`traffic_score`:** หา Percentile จากคอลัมน์ `input_veh_total`
2.  **`truck_score`:** หา Percentile จากรถบรรทุกหนัก (ถ้าไม่มีข้อมูล ใช้ `traffic_score × 0.70`)
3.  **`elevation_score`:** หา Percentile จากค่าความสูงและความชัน แล้วเฉลี่ยรวมกัน
4.  **`rain_score`:** หา Percentile จากคอลัมน์ `พื้นที่ฝนชุก`
5.  **`operating_distance_score`:** หา Percentile จาก `operating_distance`

นำคะแนน 5 ด้านนี้ไป **คูณกับน้ำหนัก (Weights)** ประจำหมวดหมู่งาน (Profile) เช่น งานผิวทาง (Pavement Profile) ให้น้ำหนักรถบรรทุกเยอะ แต่งานท่อระบายน้ำ (Drainage Profile) ให้น้ำหนักฝนเยอะ

**สูตร Factor Index:**
```text
Factor Index = (Score_1 × Weight_1) + (Score_2 × Weight_2) + ...
```
*(ค่าที่ได้จะอยู่ในช่วง 0 ถึง 1 เสมอ)*

### Step 2.3: คำนวณ Factor Cost (งบประมาณส่วนเพิ่ม)
นำคะแนนที่ได้จาก Step 2.2 มาแปลงเป็นตัวเงิน โดยระบบกำหนดเพดานปรับเพิ่มสูงสุด (Max Factor Uplift) ไว้ เช่น `15%` (0.15)

**สูตร:**
```text
Factor Cost = Base Cost × Max Factor Uplift × Factor Index
```
*ตัวอย่าง: ถ้า Base Cost = 1,000,000 บาท, Uplift = 15%, Factor Index = 0.8*
*Factor Cost = 1,000,000 × 0.15 × 0.8 = 120,000 บาท*

### Step 2.4: สรุปงบประมาณสุทธิ (Total Budget)

**สูตร:**
```text
Total Budget = SUM(Base Cost ของทุกรายการ) 
             + SUM(Factor Cost ของทุกรายการ) 
             + Fixed Costs (เช่น ค่าเช่าเครื่องจักรที่ดึงจาก RMMS)
             + (งานตัดหญ้า คำนวณแยกตามสูตร Cluster)
```

---
**สรุปสำหรับ Developer:** 
หากต้องการดัดแปลงสูตร: 
1. แก้ Quantity / Base Data -> แก้ที่ไฟล์ `master_final.xlsx`
2. แก้ Weights ของ Factor -> แก้ที่ตัวแปร `FACTOR_PROFILES` ใน `src/config.py`
3. แก้ Logic การคูณสมการ -> แก้ที่ไฟล์ `src/calculator.py`

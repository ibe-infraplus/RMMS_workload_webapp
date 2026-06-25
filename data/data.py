import pandas as pd
import re

# 1. โหลดข้อมูลสะพาน
bridge_df = pd.read_excel(r'data\bridge_bmms.xlsx')

# แปลงคอลัมน์ความยาวสะพานให้เป็นตัวเลข และหาผลรวมของความยาวสะพานในแต่ละแขวง
bridge_df['ความยาวสะพาน (ม.)'] = pd.to_numeric(bridge_df['ความยาวสะพาน (ม.)'], errors='coerce')
bridge_grouped = bridge_df.groupby('แขวงการทาง')['ความยาวสะพาน (ม.)'].sum().reset_index()
bridge_grouped.columns = ['district_name_bridge', 'bridge_m']

# 2. โหลดข้อมูล group_data_final
group_data = pd.read_excel(r'data\group_data_final.xlsx')

# 3. ฟังก์ชันสำหรับทำความสะอาดชื่อแขวงเพื่อให้ Map กันได้ (ลบวงเล็บ, เว้นวรรค, และเปลี่ยน ขท. เป็น แขวงทางหลวง)
def clean_name(name):
    if pd.isna(name): return name
    name = re.sub(r'\(.*?\)', '', name) # ลบข้อความในวงเล็บ
    name = name.replace(' ', '') # ลบเว้นวรรค
    name = name.replace('ขท.', 'แขวงทางหลวง')
    return name

# สร้างคอลัมน์ชั่วคราวเพื่อใช้เป็น Key ในการเชื่อมข้อมูล
group_data['clean_key'] = group_data['district_name'].apply(clean_name)
bridge_grouped['clean_key'] = bridge_grouped['district_name_bridge'].apply(clean_name)

# 4. รวมข้อมูล (Merge)
merged_data = pd.merge(group_data, bridge_grouped[['clean_key', 'bridge_m']], on='clean_key', how='left')

# ลบคอลัมน์ที่ใช้เป็น Key ทิ้งเพื่อให้ข้อมูลสะอาด
merged_data = merged_data.drop(columns=['clean_key'])

# 5. บันทึกเป็นไฟล์ใหม่
merged_data.to_csv('group_data_final_with_bridge.csv', index=False)
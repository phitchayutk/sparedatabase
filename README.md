# NT2 Spare Parts Inventory

Streamlit web app สำหรับจัดการ Inventory อุปกรณ์ Spare Parts  
**AIT Managed Services | NT2 Account**

## Features
- 📊 Dashboard: KPI cards + charts แยก PID / Location
- 🔍 Search: ค้นหาด้วย SN / PID / Location / Status
- ⚙️ Admin: Deploy / Receive / Swap / Add Manual / Import Excel
- 📋 History: Audit Log ทุก action

## Stack
- **Frontend + Backend:** Streamlit
- **Database:** Google Sheets (via gspread)
- **Deploy:** Streamlit Community Cloud

## Setup

### 1. Clone repo
```bash
git clone https://github.com/YOUR_USERNAME/nt2-inventory.git
cd nt2-inventory
pip install -r requirements.txt
```

### 2. Secrets
สร้างไฟล์ `.streamlit/secrets.toml` (ดู template ด้านล่าง)

```toml
[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "..."
client_email = "..."
...

[app]
admin_password = "your_password"
sheet_url = "https://docs.google.com/spreadsheets/d/..."
```

### 3. Run
```bash
streamlit run app.py
```

## Deploy to Streamlit Cloud
1. Push code to GitHub (secrets.toml จะถูก .gitignore ไว้แล้ว)
2. ไปที่ https://share.streamlit.io → New app → เลือก repo
3. ใส่ secrets ใน App settings → Secrets

## Admin Password
Default: `nt2admin2024` (แนะนำให้เปลี่ยนใน secrets.toml)

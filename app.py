import streamlit as st
from utils.sheets import init_sheet_headers
from utils.auth import logout

st.set_page_config(
    page_title="NT2 Inventory",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Init ──────────────────────────────────────────────────────────────────────
if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False
if "admin_name" not in st.session_state:
    st.session_state["admin_name"] = ""

init_sheet_headers()

# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/53/NT_logo.svg/320px-NT_logo.svg.png", width=120)
    st.markdown("## 📦 NT2 Inventory")
    st.markdown("---")

    if st.session_state["is_admin"]:
        st.success(f"🔓 Admin Mode")
        if st.button("🚪 Logout"):
            logout()
            st.rerun()
    else:
        st.info("👁️ View Only Mode")

    st.markdown("---")
    st.caption("AIT Managed Services | NT2 Account")

# ─── Home page ────────────────────────────────────────────────────────────────
st.title("📦 NT2 Spare Parts Inventory")
st.markdown("""
ระบบจัดการ Inventory อุปกรณ์ Spare Parts สำหรับ NT2 Account  
**AIT Managed Services Team**

---

### เมนูหลัก

| หน้า | คำอธิบาย |
|---|---|
| 📊 **Dashboard** | ภาพรวมสถานะอุปกรณ์ทั้งหมด |
| 🔍 **Search** | ค้นหาอุปกรณ์ด้วย SN / PID / Location |
| ⚙️ **Admin** | จัดการข้อมูล (Deploy / Receive / Swap / Import) |
| 📋 **History** | ดู Audit Log การเปลี่ยนแปลงทั้งหมด |

---
""")

col1, col2, col3 = st.columns(3)
with col1:
    st.info("👈 ใช้เมนูด้านซ้ายเพื่อเปลี่ยนหน้า")
with col2:
    st.info("🔐 Admin ต้อง Login ก่อนแก้ไขข้อมูล")
with col3:
    st.info("📊 ข้อมูล Sync Real-time กับ Google Sheets")

import streamlit as st
from utils.sheets import init_sheet_headers
from utils.auth import logout

st.set_page_config(
    page_title="NT2 Inventory | AIT",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": None,
        "Report a bug": None,
        "About": "NT2 Spare Parts Inventory | AIT Managed Services"
    }
)

if "is_admin" not in st.session_state:
    st.session_state["is_admin"] = False
if "admin_name" not in st.session_state:
    st.session_state["admin_name"] = ""

try:
    init_sheet_headers()
except:
    pass

with st.sidebar:
    st.markdown("## 📦 NT2 Inventory")
    st.markdown("**AIT Managed Services**")
    st.markdown("---")
    if st.session_state["is_admin"]:
        st.success("🔓 Admin Mode")
        if st.button("🚪 Logout"):
            logout()
            st.rerun()
    else:
        st.info("👁️ View Only Mode")
    st.markdown("---")
    st.caption("NT2 Account | Spare Parts System")

st.markdown("""
<style>
.home-card {
    background: #f8f9fa;
    border-radius: 12px;
    padding: 20px 24px;
    border-left: 5px solid #5B9BD5;
    margin-bottom: 12px;
    font-size: 16px;
}
.home-card h3 { margin: 0 0 6px 0; color: #1a1a2e; }
.home-card p  { margin: 0; color: #555; }
</style>
""", unsafe_allow_html=True)

st.title("📦 NT2 Spare Parts Inventory")
st.markdown("ระบบจัดการ Inventory อุปกรณ์ Spare Parts | **NT2MA Team**")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    <div class="home-card">
        <h3>📊 Dashboard</h3>
        <p>ภาพรวมสถานะอุปกรณ์ทั้งหมด KPI + Charts แยก PID</p>
    </div>
    <div class="home-card">
        <h3>🔍 Search</h3>
        <p>ค้นหาอุปกรณ์ด้วย SN / PID / Location / Status</p>
    </div>
    <div class="home-card">
        <h3>📡 Device in TOR</h3>
        <p>ตารางอุปกรณ์ใน TOR แยก PE / LPE ค้นหาและ Export ได้</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="home-card">
        <h3>⚙️ Admin</h3>
        <p>Deploy / Receive / Swap / Add Manual / Import Excel</p>
    </div>
    <div class="home-card">
        <h3>📋 History</h3>
        <p>Audit Log บันทึกการเปลี่ยนแปลงทุก Action</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.info("👈 เลือกเมนูด้านซ้ายเพื่อเริ่มใช้งาน  |  🔐 Admin Login ที่หน้า Admin Panel")

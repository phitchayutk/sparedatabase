import streamlit as st
import pandas as pd
import io
from utils.auth import login_form, logout
from utils.inventory import deploy_device, receive_device, swap_device, bulk_import, edit_device, delete_device
from utils.sheets import load_inventory

st.set_page_config(page_title="Admin", page_icon="⚙️", layout="wide")
st.title("⚙️ Admin Panel")

# ─── Auth gate ────────────────────────────────────────────────────────────────
is_admin = login_form()
if not is_admin:
    st.warning("🔐 กรุณา Login เพื่อเข้าใช้งาน Admin Panel")
    st.stop()

admin_name = st.session_state.get("admin_name", "Admin")
st.success(f"🔓 เข้าสู่ระบบในฐานะ: {admin_name}")

if st.button("🚪 Logout", key="admin_logout"):
    logout()
    st.rerun()

st.markdown("---")

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🚀 Deploy", "📥 Receive", "🔄 Swap", "➕ Add Manual", "📤 Import Excel", "✏️ Edit / Delete"
])

# ── Tab 1: Deploy ──────────────────────────────────────────────────────────────
with tab1:
    st.markdown("### 🚀 นำอุปกรณ์ออกใช้งาน")
    st.info("เปลี่ยน Status จาก Available → Disable และบันทึก Location / Ticket")
    with st.form("deploy_form"):
        sn = st.text_input("Serial Number (SN) *", placeholder="เช่น CAT1940V0NM")
        location = st.text_input("Location ปลายทาง *", placeholder="เช่น nrt_trg_lpe1")
        case_ticket = st.text_input("Case Ticket", placeholder="เช่น 2332")
        submitted = st.form_submit_button("🚀 Deploy")
        if submitted:
            if not sn or not location:
                st.error("กรุณากรอก SN และ Location")
            else:
                ok, msg = deploy_device(sn, location, case_ticket, admin_name)
                st.success(msg) if ok else st.error(msg)

# ── Tab 2: Receive ─────────────────────────────────────────────────────────────
with tab2:
    st.markdown("### 📥 นำอุปกรณ์เข้าระบบ")
    st.info("เพิ่มอุปกรณ์ใหม่เข้า Inventory พร้อม Status Available")

    df_now = load_inventory()
    pid_choices = sorted(df_now["PID"].dropna().unique().tolist()) if not df_now.empty else []
    pid_choices = pid_choices + ["อื่นๆ (พิมพ์เอง)"]

    with st.form("receive_form"):
        pid_sel = st.selectbox("PID *", pid_choices)
        pid_custom = st.text_input("PID (พิมพ์เอง ถ้าเลือก 'อื่นๆ')", placeholder="เช่น ASR-920-24SZ-IM V01")
        sn = st.text_input("Serial Number (SN) *", placeholder="เช่น CAT1941V17T")
        source = st.text_input("ได้รับมาจาก", placeholder="เช่น pkn_bso_lpe1 หรือ Cisco TAC")
        location = st.text_input("Location เริ่มต้น", placeholder="เช่น SC-SRT")
        remark = st.text_input("Remark", placeholder="หมายเหตุ")
        submitted = st.form_submit_button("📥 รับเข้าระบบ")
        if submitted:
            pid_final = pid_custom if pid_sel == "อื่นๆ (พิมพ์เอง)" else pid_sel
            if not pid_final or not sn:
                st.error("กรุณากรอก PID และ SN")
            else:
                ok, msg = receive_device(pid_final, sn, source, location, remark, admin_name)
                st.success(msg) if ok else st.error(msg)

# ── Tab 3: Swap ────────────────────────────────────────────────────────────────
with tab3:
    st.markdown("### 🔄 เปลี่ยนอุปกรณ์ (Swap)")
    st.info("Deploy ตัวใหม่ออกไป + รับตัวเสียกลับเข้า Inventory")
    with st.form("swap_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**ตัวใหม่ที่ Deploy ออกไป**")
            new_sn = st.text_input("SN ตัวใหม่ *", placeholder="เช่น CAT1940V0NM")
            location = st.text_input("Location *", placeholder="เช่น nrt_trg_lpe1")
            case_ticket = st.text_input("Case Ticket", placeholder="เช่น 2332")
        with col2:
            st.markdown("**ตัวเสียที่รับกลับมา**")
            faulty_sn = st.text_input("SN ตัวเสีย *", placeholder="เช่น CAT1940V0D2")
            faulty_code = st.text_input("Faulty Code", placeholder="เช่น CAT2438U09F")
        submitted = st.form_submit_button("🔄 Swap")
        if submitted:
            if not new_sn or not faulty_sn or not location:
                st.error("กรุณากรอกข้อมูลที่จำเป็น (*)")
            else:
                ok, msg = swap_device(new_sn, faulty_sn, location, case_ticket, faulty_code, admin_name)
                st.success(msg) if ok else st.error(msg)

# ── Tab 4: Add Manual ──────────────────────────────────────────────────────────
with tab4:
    st.markdown("### ➕ Add อุปกรณ์ Manual")
    with st.form("manual_add_form"):
        col1, col2 = st.columns(2)
        with col1:
            m_pid = st.text_input("PID *", placeholder="เช่น ASR-920-12SZ-D V01")
            m_sn = st.text_input("SN *", placeholder="เช่น CAT2346U35F")
            m_source = st.text_input("ได้รับมาจาก", placeholder="เช่น pbi_nyp_lpe1")
            m_status = st.selectbox("Status", ["Available", "Disable", "Faulty"])
        with col2:
            m_location = st.text_input("Location", placeholder="เช่น SC-SRT หรือ nyk_scl_lpe1")
            m_ticket = st.text_input("Case Ticket", placeholder="เช่น 2327")
            m_faulty = st.text_input("Faulty Code", placeholder="เช่น CAT2438U03U")
            m_remark = st.text_input("Remark")
        submitted = st.form_submit_button("➕ เพิ่มอุปกรณ์")
        if submitted:
            if not m_pid or not m_sn:
                st.error("กรุณากรอก PID และ SN")
            else:
                from utils.sheets import load_inventory, save_inventory, append_audit
                import pandas as pd
                df_c = load_inventory()
                if m_sn.strip().upper() in df_c["SN"].str.upper().values:
                    st.error(f"SN {m_sn} มีอยู่ในระบบแล้ว")
                else:
                    new_row = {"No": len(df_c)+1, "PID": m_pid, "SN": m_sn, "ได้รับมาจาก": m_source,
                               "Status": m_status, "Location": m_location, "Case Ticket": m_ticket,
                               "Faulty": m_faulty, "Remark": m_remark}
                    df_c = pd.concat([df_c, pd.DataFrame([new_row])], ignore_index=True)
                    save_inventory(df_c)
                    append_audit("ManualAdd", m_sn, m_pid, f"เพิ่มด้วย Manual | Status: {m_status}", admin_name)
                    st.success(f"✅ เพิ่ม {m_sn} สำเร็จ")

# ── Tab 5: Import Excel ────────────────────────────────────────────────────────
with tab5:
    st.markdown("### 📤 Import จาก Excel")

    # Template download
    template_cols = ["PID", "SN", "ได้รับมาจาก", "Status", "Location", "Case Ticket", "Faulty", "Remark"]
    sample_data = [
        ["ASR-920-12SZ-D V01", "CAT2332U3A0", "pbi_nyp_lpe1", "Disable", "ssk_whn_lpe1", "2309", "CAT2438U09F", "ของเสียคืนแล้ว"],
        ["ASR-920-24SZ-IM V01", "CAT1938V0NM", "acr_cnm_lpe1", "Available", "SC-SRT", "", "", ""],
    ]
    df_template = pd.DataFrame(sample_data, columns=template_cols)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df_template.to_excel(writer, index=False, sheet_name="inventory")
    st.download_button(
        "⬇️ Download Excel Template",
        buf.getvalue(),
        "inventory_template.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.markdown("---")
    uploaded = st.file_uploader("อัปโหลดไฟล์ Excel (.xlsx)", type=["xlsx"])
    if uploaded:
        preview_df = pd.read_excel(uploaded)
        st.markdown("**Preview (5 rows แรก):**")
        st.dataframe(preview_df.head(5), use_container_width=True)

        if st.button("✅ ยืนยัน Import"):
            uploaded.seek(0)
            ok, msg = bulk_import(uploaded, admin_name)
            st.success(msg) if ok else st.error(msg)

# ── Tab 6: Edit / Delete ───────────────────────────────────────────────────────
with tab6:
    st.markdown("### ✏️ แก้ไข / ลบอุปกรณ์")
    sn_edit = st.text_input("ใส่ SN ที่ต้องการแก้ไข", key="edit_sn")

    if sn_edit:
        df_e = load_inventory()
        row = df_e[df_e["SN"].str.upper() == sn_edit.strip().upper()]
        if row.empty:
            st.error(f"ไม่พบ SN: {sn_edit}")
        else:
            r = row.iloc[0]
            with st.form("edit_form"):
                col1, col2 = st.columns(2)
                with col1:
                    e_status = st.selectbox("Status", ["Available", "Disable", "Faulty"],
                                            index=["Available", "Disable", "Faulty"].index(r["Status"]) if r["Status"] in ["Available", "Disable", "Faulty"] else 0)
                    e_location = st.text_input("Location", value=str(r["Location"]))
                    e_ticket = st.text_input("Case Ticket", value=str(r["Case Ticket"]))
                with col2:
                    e_faulty = st.text_input("Faulty Code", value=str(r["Faulty"]))
                    e_source = st.text_input("ได้รับมาจาก", value=str(r["ได้รับมาจาก"]))
                    e_remark = st.text_input("Remark", value=str(r["Remark"]))

                col_save, col_del = st.columns(2)
                with col_save:
                    save_btn = st.form_submit_button("💾 บันทึก")
                with col_del:
                    del_btn = st.form_submit_button("🗑️ ลบ", type="secondary")

                if save_btn:
                    updates = {"Status": e_status, "Location": e_location, "Case Ticket": e_ticket,
                               "Faulty": e_faulty, "ได้รับมาจาก": e_source, "Remark": e_remark}
                    ok, msg = edit_device(sn_edit, updates, admin_name)
                    st.success(msg) if ok else st.error(msg)

                if del_btn:
                    ok, msg = delete_device(sn_edit, admin_name)
                    st.success(msg) if ok else st.error(msg)

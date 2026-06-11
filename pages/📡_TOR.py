import streamlit as st
import pandas as pd
import io
from utils.sheets import get_sheet, _force_string_df
from utils.auth import login_form

st.set_page_config(page_title="Device in TOR", page_icon="📡", layout="wide")
st.title("📡 Device in TOR")

PE_COLS  = ["No.", "Hostname", "ชื่อรุ่นอุปกรณ์", "Collected SN", "จังหวัด",
            "ศูนย์ระบบบำรุงรักษากลาง", "ระยะทางจากศูนย์ กรุงเทพฯ (กิโลเมตร)",
            "ระยะทางจากศูนย์ ภูมิภาค (กิโลเมตร)", "ภาคผนวก", "Project"]
LPE_COLS = ["ลำดับที่", "Hostname", "ชื่อรุ่นอุปกรณ์", "Collected SN", "จังหวัด",
            "ศูนย์ระบบบำรุงรักษากลาง",
            "ระยะทางจากศูนย์ระบบบำรุงรักษากลาง (กิโลเมตร)", "ภาคผนวก", "Project"]

@st.cache_data(ttl=60)
def load_tor(tab, cols):
    try:
        ws   = get_sheet(tab)
        data = ws.get_all_records(numericise_ignore=["all"])
        if not data:
            return pd.DataFrame(columns=cols)
        return _force_string_df(pd.DataFrame(data), cols)
    except Exception as e:
        st.error(f"โหลด {tab} ไม่ได้: {e}")
        return pd.DataFrame(columns=cols)

def save_tor(tab, df, cols):
    ws  = get_sheet(tab)
    _df = _force_string_df(df.copy(), cols)
    ws.clear()
    ws.update([_df.columns.tolist()] + _df.values.tolist())
    load_tor.clear()

if "tor_msg" in st.session_state and st.session_state["tor_msg"]:
    msg, ok = st.session_state["tor_msg"]
    st.success(msg) if ok else st.error(msg)
    st.session_state["tor_msg"] = None

with st.spinner("กำลังโหลดข้อมูล..."):
    df_pe  = load_tor("tor_pe",  PE_COLS)
    df_lpe = load_tor("tor_lpe", LPE_COLS)

all_projects = sorted(set(
    df_pe["Project"].dropna().unique().tolist() +
    df_lpe["Project"].dropna().unique().tolist()
))
all_projects = [p for p in all_projects if p.strip()]

col_p, col_s = st.columns([2, 3])
with col_p:
    sel_project = st.selectbox("📋 Project", ["ทั้งหมด"] + all_projects)
with col_s:
    keyword = st.text_input(
        "keyword",
        placeholder="ค้นหา Hostname / SN / รุ่น / จังหวัด / ภาคผนวก...",
        label_visibility="collapsed"
    )

def apply_filter(df, project, kw):
    out = df.copy()
    if project != "ทั้งหมด":
        out = out[out["Project"] == project]
    if kw.strip():
        k = kw.strip().upper()
        mask = out.apply(
            lambda row: row.astype(str).str.upper().str.contains(k, na=False).any(), axis=1
        )
        out = out[mask]
    return out

pe_filtered  = apply_filter(df_pe,  sel_project, keyword)
lpe_filtered = apply_filter(df_lpe, sel_project, keyword)

tab_pe, tab_lpe, tab_import = st.tabs([
    f"🔵 PE ({len(pe_filtered)} รายการ)",
    f"🟢 LPE ({len(lpe_filtered)} รายการ)",
    "📤 Import / Admin"
])

with tab_pe:
    if pe_filtered.empty:
        st.info("ไม่พบข้อมูล")
    else:
        st.dataframe(
            pe_filtered.reset_index(drop=True),
            use_container_width=True, hide_index=True,
            column_config={c: st.column_config.TextColumn(c) for c in PE_COLS},
            height=500
        )
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            pe_filtered.to_excel(w, index=False, sheet_name="PE")
        st.download_button("⬇️ Export PE", buf.getvalue(), "tor_pe.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with tab_lpe:
    if lpe_filtered.empty:
        st.info("ไม่พบข้อมูล")
    else:
        st.dataframe(
            lpe_filtered.reset_index(drop=True),
            use_container_width=True, hide_index=True,
            column_config={c: st.column_config.TextColumn(c) for c in LPE_COLS},
            height=500
        )
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            lpe_filtered.to_excel(w, index=False, sheet_name="LPE")
        st.download_button("⬇️ Export LPE", buf.getvalue(), "tor_lpe.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with tab_import:
    st.markdown("### 📤 Import / Admin")

    if not st.session_state.get("is_admin"):
        st.warning("🔐 กรุณา Login ที่หน้า Admin ก่อนครับ")
        st.markdown("👈 ไปที่เมนู **Admin** → Login → กลับมาหน้านี้")
    else:
        st.success(f"🔓 Admin: {st.session_state.get('admin_name', 'Admin')}")

        buf_tmpl = io.BytesIO()
        with pd.ExcelWriter(buf_tmpl, engine="openpyxl") as w:
            pd.DataFrame(columns=PE_COLS).to_excel(w, index=False, sheet_name="PE")
            pd.DataFrame(columns=LPE_COLS).to_excel(w, index=False, sheet_name="LPE")
        st.download_button("⬇️ Download Template", buf_tmpl.getvalue(), "tor_template.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        st.markdown("---")
        import_mode = st.radio("วิธี Import",
                                ["เพิ่มต่อท้าย (Append)", "แทนที่ทั้งหมด (Replace)"],
                                horizontal=True, key="tor_mode")
        uploaded = st.file_uploader("อัปโหลดไฟล์ Excel (.xlsx)", type=["xlsx"], key="tor_upload")

        if uploaded:
            xl = pd.ExcelFile(uploaded)
            found_pe  = "PE"  in xl.sheet_names
            found_lpe = "LPE" in xl.sheet_names

            if not found_pe and not found_lpe:
                st.error("ไม่พบ Sheet PE หรือ LPE ในไฟล์")
            else:
                if found_pe:
                    st.markdown("**Preview PE (3 rows):**")
                    st.dataframe(pd.read_excel(xl, sheet_name="PE", nrows=3), use_container_width=True)
                if found_lpe:
                    st.markdown("**Preview LPE (3 rows):**")
                    st.dataframe(pd.read_excel(xl, sheet_name="LPE", nrows=3), use_container_width=True)

                if st.button("✅ ยืนยัน Import", key="btn_tor_import"):
                    try:
                        added_pe = added_lpe = 0
                        if found_pe:
                            new_pe = pd.read_excel(xl, sheet_name="PE", dtype=str).fillna("")
                            final_pe = new_pe if import_mode.startswith("แทนที่") else \
                                pd.concat([df_pe, new_pe], ignore_index=True).drop_duplicates(subset=["Hostname"])
                            save_tor("tor_pe", final_pe, PE_COLS)
                            added_pe = len(new_pe)
                        if found_lpe:
                            new_lpe = pd.read_excel(xl, sheet_name="LPE", dtype=str).fillna("")
                            final_lpe = new_lpe if import_mode.startswith("แทนที่") else \
                                pd.concat([df_lpe, new_lpe], ignore_index=True).drop_duplicates(subset=["Hostname"])
                            save_tor("tor_lpe", final_lpe, LPE_COLS)
                            added_lpe = len(new_lpe)
                        st.session_state["tor_msg"] = (
                            f"✅ Import สำเร็จ | PE: {added_pe} rows | LPE: {added_lpe} rows", True)
                        st.rerun()
                    except Exception as e:
                        st.session_state["tor_msg"] = (f"❌ Error: {e}", False)
                        st.rerun()

        st.markdown("---")
        st.markdown("### 🗑️ ล้างข้อมูล")

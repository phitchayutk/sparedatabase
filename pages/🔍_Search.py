import streamlit as st
import pandas as pd
from utils.sheets import load_inventory, load_audit
import io

st.set_page_config(page_title="Search", page_icon="🔍", layout="wide")
st.title("🔍 ค้นหาอุปกรณ์")

with st.spinner("กำลังโหลดข้อมูล..."):
    df = load_inventory()

if df.empty:
    st.warning("ยังไม่มีข้อมูลในระบบ")
    st.stop()

st.markdown("### 🔎 ค้นหา")
col_s, col_f = st.columns([3, 1])
with col_s:
    keyword = st.text_input(
        "keyword", placeholder="พิมพ์อะไรก็ได้ เช่น SN / PID / Location / Remark / Case Ticket...",
        label_visibility="collapsed"
    )
with col_f:
    status_filter = st.selectbox("Status", ["ทั้งหมด", "Available", "Disable", "Faulty"],
                                  label_visibility="collapsed")

filtered = df.copy()
if status_filter != "ทั้งหมด":
    filtered = filtered[filtered["Status"] == status_filter]
if keyword.strip():
    kw = keyword.strip().upper()
    mask = filtered.apply(
        lambda row: row.astype(str).str.upper().str.contains(kw, na=False).any(), axis=1
    )
    filtered = filtered[mask]

st.markdown(f"### ผลการค้นหา ({len(filtered)} รายการ)")
if filtered.empty:
    st.info("ไม่พบข้อมูลที่ค้นหา")
else:
    def highlight_status(row):
        colors = {"Available": "#d4edda", "Disable": "#f8d7da", "Faulty": "#fff3cd"}
        bg = colors.get(row["Status"], "#ffffff")
        return [f"background-color: {bg}"] * len(row)

    inv_cols = ["No","PID","SN","ได้รับมาจาก","Status","Location","Case Ticket","Faulty","Remark"]
    st.dataframe(
        filtered.style.apply(highlight_status, axis=1),
        use_container_width=True, hide_index=True,
        column_config={c: st.column_config.TextColumn(c) for c in inv_cols}
    )
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        csv = filtered.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ Export CSV", csv, "search_result.csv", "text/csv")
    with c2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            filtered.to_excel(w, index=False, sheet_name="SearchResult")
        st.download_button("⬇️ Export Excel", buf.getvalue(), "search_result.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.markdown("---")
st.markdown("### 📋 ดูรายละเอียด SN + ประวัติ")
sn_detail = st.text_input("ใส่ SN เพื่อดูข้อมูลและประวัติ", key="sn_detail")

if sn_detail:
    row = df[df["SN"].str.upper() == sn_detail.strip().upper()]
    if row.empty:
        st.error(f"ไม่พบ SN: {sn_detail}")
    else:
        r = row.iloc[0]
        status_icon = {"Available": "✅", "Disable": "🔴", "Faulty": "⚠️"}.get(r["Status"], "❓")
        col_info, col_hist = st.columns([1, 2])

        with col_info:
            st.markdown("#### 📦 ข้อมูลปัจจุบัน")
            st.markdown(f"""
| Field | Value |
|---|---|
| **PID** | {r['PID']} |
| **SN** | {r['SN']} |
| **Status** | {status_icon} {r['Status']} |
| **Location** | {r['Location']} |
| **ได้รับมาจาก** | {r['ได้รับมาจาก']} |
| **Case Ticket** | {r['Case Ticket']} |
| **Faulty Code** | {r['Faulty']} |
| **Remark** | {r['Remark']} |
""")

        with col_hist:
            st.markdown("#### 🕐 ประวัติการเปลี่ยนแปลง")
            audit_df = load_audit()
            if audit_df.empty or "SN" not in audit_df.columns:
                st.info("ยังไม่มีประวัติ")
            else:
                sn_log = audit_df[
                    audit_df["SN"].str.upper() == sn_detail.strip().upper()
                ].iloc[::-1].reset_index(drop=True)

                if sn_log.empty:
                    st.info("ยังไม่มีประวัติสำหรับ SN นี้")
                else:
                    action_icon = {
                        "Deploy": "🚀", "Receive": "📥", "Swap": "🔄",
                        "Edit": "✏️", "ManualAdd": "➕", "BulkImport": "📤",
                        "Delete": "🗑️",
                    }
                    for _, log in sn_log.iterrows():
                        icon = action_icon.get(log["Action"], "📌")
                        st.markdown(f"""
<div style="border-left:4px solid #5B9BD5; padding:10px 16px; margin:8px 0;
            background:#f8f9fa; border-radius:0 10px 10px 0;">
  <div style="font-weight:700; font-size:16px;">{icon} {log['Action']}
    <span style="color:#888; font-size:13px; font-weight:400; margin-left:10px;">{log['Timestamp']}</span>
  </div>
  <div style="font-size:14px; color:#333; margin-top:4px;">{log['Detail']}</div>
  <div style="font-size:12px; color:#999; margin-top:2px;">โดย: {log['Performed By']}</div>
</div>""", unsafe_allow_html=True)

import streamlit as st
import pandas as pd
from utils.sheets import load_inventory
import io

st.set_page_config(page_title="Search", page_icon="🔍", layout="wide")
st.title("🔍 ค้นหาอุปกรณ์")

with st.spinner("กำลังโหลดข้อมูล..."):
    df = load_inventory()

if df.empty:
    st.warning("ยังไม่มีข้อมูลในระบบ")
    st.stop()

# ─── Search filters ───────────────────────────────────────────────────────────
st.markdown("### ตัวกรองการค้นหา")
col1, col2, col3, col4 = st.columns(4)

with col1:
    search_sn = st.text_input("🔎 Serial Number (SN)", placeholder="เช่น CAT2332U3A0")
with col2:
    pid_options = ["ทั้งหมด"] + sorted(df["PID"].dropna().unique().tolist())
    search_pid = st.selectbox("📦 Product ID (PID)", pid_options)
with col3:
    loc_options = ["ทั้งหมด"] + sorted(df["Location"].dropna().unique().tolist())
    search_loc = st.selectbox("📍 Location", loc_options)
with col4:
    status_options = ["ทั้งหมด", "Available", "Disable", "Faulty"]
    search_status = st.selectbox("🚦 Status", status_options)

# ─── Apply filters ────────────────────────────────────────────────────────────
filtered = df.copy()

if search_sn:
    filtered = filtered[filtered["SN"].str.upper().str.contains(search_sn.strip().upper(), na=False)]
if search_pid != "ทั้งหมด":
    filtered = filtered[filtered["PID"] == search_pid]
if search_loc != "ทั้งหมด":
    filtered = filtered[filtered["Location"] == search_loc]
if search_status != "ทั้งหมด":
    filtered = filtered[filtered["Status"] == search_status]

# ─── Results ──────────────────────────────────────────────────────────────────
st.markdown(f"### ผลการค้นหา ({len(filtered)} รายการ)")

if filtered.empty:
    st.info("ไม่พบข้อมูลที่ค้นหา")
else:
    # Color-code status
    def highlight_status(row):
        if row["Status"] == "Available":
            return ["background-color: #d4edda"] * len(row)
        elif row["Status"] == "Disable":
            return ["background-color: #f8d7da"] * len(row)
        elif row["Status"] == "Faulty":
            return ["background-color: #fff3cd"] * len(row)
        return [""] * len(row)

    st.dataframe(
        filtered.style.apply(highlight_status, axis=1),
        use_container_width=True,
        hide_index=True
    )

    # ─── Export ───────────────────────────────────────────────────────────────
    st.markdown("---")
    col_exp1, col_exp2 = st.columns(2)
    with col_exp1:
        csv = filtered.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ Export CSV", csv, "search_result.csv", "text/csv")
    with col_exp2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            filtered.to_excel(writer, index=False, sheet_name="SearchResult")
        st.download_button(
            "⬇️ Export Excel",
            buf.getvalue(),
            "search_result.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ─── SN Detail Card ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 🔎 ดูรายละเอียด SN")
sn_detail = st.text_input("ใส่ SN เพื่อดูรายละเอียดและประวัติ", key="sn_detail_input")
if sn_detail:
    row = df[df["SN"].str.upper() == sn_detail.strip().upper()]
    if row.empty:
        st.error(f"ไม่พบ SN: {sn_detail}")
    else:
        r = row.iloc[0]
        status_icon = {"Available": "✅", "Disable": "🔴", "Faulty": "⚠️"}.get(r["Status"], "❓")
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

import streamlit as st
import pandas as pd
from utils.sheets import load_audit

st.set_page_config(page_title="History", page_icon="📋", layout="wide")
st.title("📋 Audit Log / History")

with st.spinner("กำลังโหลด Audit Log..."):
    df = load_audit()

AUDIT_COLS = ["Timestamp", "Action", "SN", "PID", "Detail", "Performed By"]

if df.empty or not all(c in df.columns for c in AUDIT_COLS):
    st.info("ยังไม่มี Log การเปลี่ยนแปลง")
    st.stop()

# ─── Filters ──────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
with col1:
    action_opts = ["ทั้งหมด"] + sorted(df["Action"].dropna().unique().tolist())
    filter_action = st.selectbox("Action", action_opts)
with col2:
    filter_sn = st.text_input("SN", placeholder="ค้นหาด้วย SN")
with col3:
    filter_by = st.text_input("Performed By")

filtered = df.copy()
if filter_action != "ทั้งหมด":
    filtered = filtered[filtered["Action"] == filter_action]
if filter_sn:
    filtered = filtered[filtered["SN"].str.upper().str.contains(filter_sn.strip().upper(), na=False)]
if filter_by:
    filtered = filtered[filtered["Performed By"].str.contains(filter_by.strip(), na=False)]

# ─── Show log (newest first) ──────────────────────────────────────────────────
st.markdown(f"### แสดง {len(filtered)} รายการ (ล่าสุดก่อน)")
st.dataframe(filtered.iloc[::-1].reset_index(drop=True), use_container_width=True, hide_index=True)

# ─── Export ───────────────────────────────────────────────────────────────────
csv = filtered.to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ Export Audit Log CSV", csv, "audit_log.csv", "text/csv")

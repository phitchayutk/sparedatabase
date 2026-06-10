import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils.sheets import load_inventory

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

st.markdown("""
<style>
.kpi-card {
    background: #ffffff;
    border-radius: 16px;
    padding: 24px 20px;
    text-align: center;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    border-top: 5px solid #ccc;
}
.kpi-card.total   { border-top-color: #5B9BD5; }
.kpi-card.avail   { border-top-color: #2ECC71; }
.kpi-card.disable { border-top-color: #E74C3C; }
.kpi-card.faulty  { border-top-color: #F39C12; }
.kpi-card.util    { border-top-color: #9B59B6; }
.kpi-label { font-size: 15px; font-weight: 600; color: #666; margin-bottom: 8px; }
.kpi-value { font-size: 52px; font-weight: 800; line-height: 1.1; color: #1a1a2e; }
.kpi-sub   { font-size: 13px; color: #999; margin-top: 4px; }
.section-title {
    font-size: 20px; font-weight: 700; color: #1a1a2e;
    margin: 16px 0 12px 0; padding-left: 10px;
    border-left: 4px solid #5B9BD5;
}
.rank-item {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 16px; margin: 6px 0;
    border-radius: 10px; background: #f8f9fa;
    font-size: 15px;
}
.rank-num  { font-weight: 800; color: #5B9BD5; font-size: 18px; width: 28px; }
.rank-pid  { flex: 1; font-weight: 600; color: #1a1a2e; padding: 0 10px; }
.rank-count{ font-weight: 800; font-size: 20px; color: #2ECC71; }
</style>
""", unsafe_allow_html=True)

st.markdown("# 📊 NT2 Inventory Dashboard")
st.caption("ข้อมูล Spare Parts | AIT Managed Services")

with st.spinner("กำลังโหลดข้อมูล..."):
    df = load_inventory()

if df.empty:
    st.warning("ยังไม่มีข้อมูลในระบบ กรุณา Import ข้อมูลก่อน")
    st.stop()

# ─── KPI ──────────────────────────────────────────────────────────────────────
total     = len(df)
available = len(df[df["Status"] == "Available"])
disabled  = len(df[df["Status"] == "Disable"])
faulty    = len(df[df["Status"] == "Faulty"])
util_rate = round(disabled / total * 100, 1) if total > 0 else 0

c1, c2, c3, c4, c5 = st.columns(5)
for col, cls, label, val, sub in [
    (c1, "total",   "📦 Total",       total,         "รายการทั้งหมด"),
    (c2, "avail",   "✅ Available",    available,     "พร้อมใช้งาน"),
    (c3, "disable", "🔴 Disable",      disabled,      "กำลังใช้งานอยู่"),
    (c4, "faulty",  "⚠️ Faulty",       faulty,        "อุปกรณ์เสีย"),
    (c5, "util",    "📈 Utilization",  f"{util_rate}%","อัตราการใช้งาน"),
]:
    col.markdown(f"""
    <div class="kpi-card {cls}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{val}</div>
        <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Section 1: Pie + Top 10 Available ────────────────────────────────────────
st.markdown('<div class="section-title">สถานะอุปกรณ์รวม</div>', unsafe_allow_html=True)

col_pie, col_top = st.columns([1, 1])

with col_pie:
    color_map = {"Available": "#2ECC71", "Disable": "#E74C3C", "Faulty": "#F39C12"}
    status_counts = df["Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    fig_pie = px.pie(
        status_counts, values="Count", names="Status",
        color="Status", color_discrete_map=color_map, hole=0.45,
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label", textfont_size=17)
    fig_pie.update_layout(
        height=400,
        legend=dict(font=dict(size=15)),
        margin=dict(t=20, b=20, l=20, r=20)
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_top:
    st.markdown("#### 🏆 Top 10 PID — Available มากที่สุด")
    avail_df = df[df["Status"] == "Available"]
    if not avail_df.empty:
        # Group by PID prefix (เอาแค่ชื่อหลัก ตัด version ออก)
        top10 = (avail_df.groupby("PID").size()
                 .reset_index(name="Count")
                 .sort_values("Count", ascending=False)
                 .head(10)
                 .reset_index(drop=True))
        rank_html = ""
        for i, row in top10.iterrows():
            medal = ["🥇","🥈","🥉"][i] if i < 3 else f"{i+1}."
            rank_html += f"""
            <div class="rank-item">
                <span class="rank-num">{medal}</span>
                <span class="rank-pid">{row['PID']}</span>
                <span class="rank-count">{row['Count']}</span>
            </div>"""
        st.markdown(rank_html, unsafe_allow_html=True)
    else:
        st.info("ไม่มีอุปกรณ์ Available")

st.markdown("<br>", unsafe_allow_html=True)

# ─── Section 2: ตารางสรุปแยก PID ─────────────────────────────────────────────
st.markdown('<div class="section-title">ตารางสรุปแยก PID</div>', unsafe_allow_html=True)

summary_pid = df.groupby(["PID", "Status"]).size().unstack(fill_value=0).reset_index()
for s in ["Available", "Disable", "Faulty"]:
    if s not in summary_pid.columns:
        summary_pid[s] = 0
summary_pid["Total"] = summary_pid[["Available", "Disable", "Faulty"]].sum(axis=1)
summary_pid["% Available"] = (summary_pid["Available"] / summary_pid["Total"] * 100).round(1).astype(str) + "%"
summary_pid = summary_pid.sort_values("Total", ascending=False).reset_index(drop=True)

def color_pid_row(row):
    pct = row["Available"] / row["Total"] if row["Total"] > 0 else 0
    bg = "#d4edda" if pct >= 0.7 else "#fff3cd" if pct >= 0.3 else "#f8d7da"
    return [f"background-color:{bg}; font-size:15px"] * len(row)

st.dataframe(
    summary_pid[["PID","Total","Available","Disable","Faulty","% Available"]]
    .style.apply(color_pid_row, axis=1),
    use_container_width=True,
    hide_index=True,
    height=min(600, 38 * (len(summary_pid) + 1) + 10),
)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Section 3: Available by PID (Top 15 bar) ────────────────────────────────
st.markdown('<div class="section-title">จำนวน Available แยกราย PID (Top 15)</div>', unsafe_allow_html=True)

avail_pid = (df[df["Status"]=="Available"]
             .groupby("PID").size()
             .reset_index(name="Count")
             .sort_values("Count", ascending=True)
             .tail(15))

fig_avail = px.bar(
    avail_pid, x="Count", y="PID", orientation="h",
    text="Count", color="Count",
    color_continuous_scale=["#a8e6cf","#2ECC71","#1a8a4a"],
)
fig_avail.update_traces(textfont_size=15, textposition="outside")
fig_avail.update_layout(
    height=max(400, len(avail_pid) * 48),
    yaxis=dict(tickfont=dict(size=14)),
    xaxis=dict(tickfont=dict(size=13), dtick=1),
    coloraxis_showscale=False,
    margin=dict(t=20, b=20, l=20, r=60),
    plot_bgcolor="rgba(0,0,0,0)",
)
fig_avail.update_yaxes(gridcolor="#f0f0f0")
st.plotly_chart(fig_avail, use_container_width=True)

# ─── Section 4: Disable by PID ────────────────────────────────────────────────
st.markdown('<div class="section-title">จำนวน Disable แยกราย PID (Top 15)</div>', unsafe_allow_html=True)

dis_pid = (df[df["Status"]=="Disable"]
           .groupby("PID").size()
           .reset_index(name="Count")
           .sort_values("Count", ascending=True)
           .tail(15))

if not dis_pid.empty:
    fig_dis = px.bar(
        dis_pid, x="Count", y="PID", orientation="h",
        text="Count", color="Count",
        color_continuous_scale=["#f5c6cb","#E74C3C","#a01010"],
    )
    fig_dis.update_traces(textfont_size=15, textposition="outside")
    fig_dis.update_layout(
        height=max(400, len(dis_pid) * 48),
        yaxis=dict(tickfont=dict(size=14)),
        xaxis=dict(tickfont=dict(size=13), dtick=1),
        coloraxis_showscale=False,
        margin=dict(t=20, b=20, l=20, r=60),
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig_dis.update_yaxes(gridcolor="#f0f0f0")
    st.plotly_chart(fig_dis, use_container_width=True)
else:
    st.info("ไม่มีอุปกรณ์ Disable")

# ─── Raw table ────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("📋 ดูข้อมูลทั้งหมด"):
    st.dataframe(df, use_container_width=True, hide_index=True)
    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Download CSV", csv, "inventory_export.csv", "text/csv")

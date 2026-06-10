import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
from datetime import datetime
import time

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_URL = "https://docs.google.com/spreadsheets/d/1cKJHRveg0jpramKW_VJPwPJGkmoZuC2OkMGdPESZAjE/edit"

INVENTORY_COLS = ["No", "PID", "SN", "ได้รับมาจาก", "Status", "Location", "Case Ticket", "Faulty", "Remark"]
AUDIT_COLS = ["Timestamp", "Action", "SN", "PID", "Detail", "Performed By"]

# Cache TTL: 60 วินาที — อ่านจาก Sheets แค่ครั้งเดียวต่อนาที
CACHE_TTL = 60


@st.cache_resource(ttl=300)
def get_client():
    """Cache Google client 5 นาที"""
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def get_sheet(tab_name: str):
    client = get_client()
    sh = client.open_by_url(SHEET_URL)
    return sh.worksheet(tab_name)


def _retry(fn, retries=3, delay=5):
    """Retry wrapper สำหรับ API call ที่อาจ rate-limit"""
    for i in range(retries):
        try:
            return fn()
        except gspread.exceptions.APIError as e:
            if "429" in str(e) and i < retries - 1:
                time.sleep(delay * (i + 1))  # backoff: 5s, 10s, 15s
            else:
                raise


# ─── Inventory ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def load_inventory() -> pd.DataFrame:
    """Cache ข้อมูล inventory 60 วินาที ลด API call"""
    try:
        def _load():
            ws = get_sheet("inventory")
            return ws.get_all_records()
        data = _retry(_load)
        if not data:
            return pd.DataFrame(columns=INVENTORY_COLS)
        df = pd.DataFrame(data)
        for col in INVENTORY_COLS:
            if col not in df.columns:
                df[col] = ""
        return df[INVENTORY_COLS]
    except Exception as e:
        st.error(f"โหลดข้อมูลไม่ได้: {e}")
        return pd.DataFrame(columns=INVENTORY_COLS)


def save_inventory(df: pd.DataFrame):
    def _save():
        ws = get_sheet("inventory")
        _df = df.copy()
        _df["No"] = range(1, len(_df) + 1)
        _df = _df.fillna("")
        ws.clear()
        ws.update([_df.columns.tolist()] + _df.values.tolist())
    _retry(_save)
    # Clear cache หลัง save เพื่อให้อ่านข้อมูลใหม่ทันที
    load_inventory.clear()


def init_sheet_headers():
    """Create headers if sheets are empty."""
    try:
        inv_ws = get_sheet("inventory")
        if not inv_ws.get_all_values():
            inv_ws.update([INVENTORY_COLS])
        audit_ws = get_sheet("audit_log")
        if not audit_ws.get_all_values():
            audit_ws.update([AUDIT_COLS])
    except Exception as e:
        st.error(f"Init sheet error: {e}")


# ─── Audit Log ────────────────────────────────────────────────────────────────

def append_audit(action: str, sn: str, pid: str, detail: str, performed_by: str):
    try:
        def _append():
            ws = get_sheet("audit_log")
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                action, sn, pid, detail, performed_by
            ]
            ws.append_row(row)
        _retry(_append)
        load_audit.clear()
    except Exception as e:
        st.warning(f"บันทึก audit log ไม่ได้: {e}")


@st.cache_data(ttl=CACHE_TTL)
def load_audit() -> pd.DataFrame:
    """Cache audit log 60 วินาที"""
    try:
        def _load():
            ws = get_sheet("audit_log")
            return ws.get_all_records()
        data = _retry(_load)
        if not data:
            return pd.DataFrame(columns=AUDIT_COLS)
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"โหลด audit log ไม่ได้: {e}")
        return pd.DataFrame(columns=AUDIT_COLS)

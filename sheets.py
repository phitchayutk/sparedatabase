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
CACHE_TTL = 60


@st.cache_resource(ttl=300)
def get_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def get_sheet(tab_name: str):
    client = get_client()
    sh = client.open_by_url(SHEET_URL)
    return sh.worksheet(tab_name)


def _retry(fn, retries=3, delay=5):
    for i in range(retries):
        try:
            return fn()
        except gspread.exceptions.APIError as e:
            if "429" in str(e) and i < retries - 1:
                time.sleep(delay * (i + 1))
            else:
                raise


def _clean_df(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    """Ensure all columns exist and are string type — prevents ArrowInvalid errors"""
    for col in cols:
        if col not in df.columns:
            df[col] = ""
    df = df[cols].copy()
    # Force everything to string to fix mixed-type pyarrow errors
    for col in cols:
        df[col] = df[col].astype(str).str.strip()
    df = df.replace({"nan": "", "None": "", "NaN": ""})
    return df


# ─── Inventory ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=CACHE_TTL)
def load_inventory() -> pd.DataFrame:
    try:
        def _load():
            ws = get_sheet("inventory")
            return ws.get_all_records(numericise_ignore=["all"])
        data = _retry(_load)
        if not data:
            return pd.DataFrame(columns=INVENTORY_COLS)
        return _clean_df(pd.DataFrame(data), INVENTORY_COLS)
    except Exception as e:
        st.error(f"โหลดข้อมูลไม่ได้: {e}")
        return pd.DataFrame(columns=INVENTORY_COLS)


def save_inventory(df: pd.DataFrame):
    def _save():
        ws = get_sheet("inventory")
        _df = df.copy().fillna("")
        _df["No"] = range(1, len(_df) + 1)
        # Convert to string for safe serialization
        for col in _df.columns:
            _df[col] = _df[col].astype(str).replace("nan", "")
        ws.clear()
        ws.update([_df.columns.tolist()] + _df.values.tolist())
    _retry(_save)
    load_inventory.clear()


def init_sheet_headers():
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
            row = [datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                   action, sn, pid, detail, performed_by]
            ws.append_row(row)
        _retry(_append)
        load_audit.clear()
    except Exception as e:
        st.warning(f"บันทึก audit log ไม่ได้: {e}")


@st.cache_data(ttl=CACHE_TTL)
def load_audit() -> pd.DataFrame:
    try:
        def _load():
            ws = get_sheet("audit_log")
            return ws.get_all_records(numericise_ignore=["all"])
        data = _retry(_load)
        if not data:
            return pd.DataFrame(columns=AUDIT_COLS)
        return _clean_df(pd.DataFrame(data), AUDIT_COLS)
    except Exception as e:
        st.error(f"โหลด audit log ไม่ได้: {e}")
        return pd.DataFrame(columns=AUDIT_COLS)

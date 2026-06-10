import pandas as pd
from utils.sheets import load_inventory, save_inventory, append_audit


# ─── Deploy (นำออกใช้งาน) ────────────────────────────────────────────────────

def deploy_device(sn: str, location: str, case_ticket: str, performed_by: str) -> tuple[bool, str]:
    df = load_inventory()
    mask = df["SN"].str.strip().str.upper() == sn.strip().upper()
    if not mask.any():
        return False, f"ไม่พบ SN: {sn}"
    idx = df[mask].index[0]
    if df.at[idx, "Status"] != "Available":
        return False, f"SN: {sn} ไม่ได้อยู่ในสถานะ Available (ปัจจุบัน: {df.at[idx, 'Status']})"

    pid = df.at[idx, "PID"]
    df.at[idx, "Status"] = "Disable"
    df.at[idx, "Location"] = location
    df.at[idx, "Case Ticket"] = case_ticket
    save_inventory(df)
    append_audit("Deploy", sn, pid, f"Deploy → {location} | Ticket: {case_ticket}", performed_by)
    return True, f"✅ Deploy {sn} → {location} สำเร็จ"


# ─── Receive (นำเข้าระบบ) ────────────────────────────────────────────────────

def receive_device(pid: str, sn: str, source: str, location: str, remark: str, performed_by: str) -> tuple[bool, str]:
    df = load_inventory()
    if sn.strip().upper() in df["SN"].str.strip().str.upper().values:
        return False, f"SN: {sn} มีอยู่ในระบบแล้ว"

    new_row = {
        "No": len(df) + 1,
        "PID": pid,
        "SN": sn.strip(),
        "ได้รับมาจาก": source,
        "Status": "Available",
        "Location": location,
        "Case Ticket": "",
        "Faulty": "",
        "Remark": remark,
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    save_inventory(df)
    append_audit("Receive", sn, pid, f"รับเข้าจาก: {source} | Location: {location}", performed_by)
    return True, f"✅ รับ {sn} เข้าระบบสำเร็จ"


# ─── Swap (เปลี่ยนอุปกรณ์) ───────────────────────────────────────────────────

def swap_device(new_sn: str, faulty_sn: str, location: str, case_ticket: str, faulty_code: str, performed_by: str) -> tuple[bool, str]:
    df = load_inventory()

    # Deploy new device
    mask_new = df["SN"].str.strip().str.upper() == new_sn.strip().upper()
    if not mask_new.any():
        return False, f"ไม่พบ SN ตัวใหม่: {new_sn}"
    idx_new = df[mask_new].index[0]
    if df.at[idx_new, "Status"] != "Available":
        return False, f"SN ตัวใหม่: {new_sn} ไม่ได้อยู่ในสถานะ Available"

    pid = df.at[idx_new, "PID"]
    df.at[idx_new, "Status"] = "Disable"
    df.at[idx_new, "Location"] = location
    df.at[idx_new, "Case Ticket"] = case_ticket
    df.at[idx_new, "Faulty"] = ""

    # Mark faulty device as returned
    mask_faulty = df["SN"].str.strip().str.upper() == faulty_sn.strip().upper()
    if mask_faulty.any():
        idx_faulty = df[mask_faulty].index[0]
        df.at[idx_faulty, "Status"] = "Faulty"
        df.at[idx_faulty, "Location"] = "SC-Stock"
        df.at[idx_faulty, "Faulty"] = faulty_code
        df.at[idx_faulty, "Remark"] = f"ตัวเสียจาก Swap | Ticket: {case_ticket}"
    else:
        # Faulty device not in system yet — add it
        new_faulty = {
            "No": len(df) + 1,
            "PID": pid,
            "SN": faulty_sn.strip(),
            "ได้รับมาจาก": "Swap Return",
            "Status": "Faulty",
            "Location": "SC-Stock",
            "Case Ticket": case_ticket,
            "Faulty": faulty_code,
            "Remark": f"ตัวเสียจาก Swap",
        }
        df = pd.concat([df, pd.DataFrame([new_faulty])], ignore_index=True)

    save_inventory(df)
    append_audit("Swap", new_sn, pid,
                 f"Swap {new_sn} → {location} | Faulty: {faulty_sn} ({faulty_code}) | Ticket: {case_ticket}",
                 performed_by)
    return True, f"✅ Swap สำเร็จ | Deploy: {new_sn} | Faulty in: {faulty_sn}"


# ─── Edit single device ───────────────────────────────────────────────────────

def edit_device(sn: str, updates: dict, performed_by: str) -> tuple[bool, str]:
    df = load_inventory()
    mask = df["SN"].str.strip().str.upper() == sn.strip().upper()
    if not mask.any():
        return False, f"ไม่พบ SN: {sn}"
    idx = df[mask].index[0]
    for col, val in updates.items():
        if col in df.columns:
            df.at[idx, col] = val
    save_inventory(df)
    append_audit("Edit", sn, df.at[idx, "PID"], f"แก้ไข: {updates}", performed_by)
    return True, f"✅ อัปเดต {sn} สำเร็จ"


# ─── Delete device ────────────────────────────────────────────────────────────

def delete_device(sn: str, performed_by: str) -> tuple[bool, str]:
    df = load_inventory()
    mask = df["SN"].str.strip().str.upper() == sn.strip().upper()
    if not mask.any():
        return False, f"ไม่พบ SN: {sn}"
    pid = df[mask].iloc[0]["PID"]
    df = df[~mask].reset_index(drop=True)
    save_inventory(df)
    append_audit("Delete", sn, pid, "ลบออกจากระบบ", performed_by)
    return True, f"✅ ลบ {sn} ออกจากระบบสำเร็จ"


# ─── Bulk import from Excel ───────────────────────────────────────────────────

def bulk_import(uploaded_file, performed_by: str) -> tuple[bool, str]:
    try:
        df_new = pd.read_excel(uploaded_file)
        # Normalize column names
        df_new.columns = [c.strip() for c in df_new.columns]
        required = ["PID", "SN"]
        for r in required:
            if r not in df_new.columns:
                return False, f"ไม่พบ column '{r}' ใน Excel"

        df_existing = load_inventory()
        existing_sns = df_existing["SN"].str.strip().str.upper().tolist()

        added, skipped = 0, 0
        rows_to_add = []
        for _, row in df_new.iterrows():
            sn = str(row.get("SN", "")).strip()
            if not sn or sn.upper() in existing_sns:
                skipped += 1
                continue
            rows_to_add.append({
                "No": 0,
                "PID": row.get("PID", ""),
                "SN": sn,
                "ได้รับมาจาก": row.get("ได้รับมาจาก", ""),
                "Status": row.get("Status", "Available"),
                "Location": row.get("Location", ""),
                "Case Ticket": row.get("Case Ticket", ""),
                "Faulty": row.get("Faulty", ""),
                "Remark": row.get("Remark", ""),
            })
            existing_sns.append(sn.upper())
            added += 1

        if rows_to_add:
            df_add = pd.DataFrame(rows_to_add)
            df_existing = pd.concat([df_existing, df_add], ignore_index=True)
            save_inventory(df_existing)
            append_audit("BulkImport", "-", "-", f"Import {added} รายการ (ข้าม {skipped} ซ้ำ)", performed_by)

        return True, f"✅ Import สำเร็จ: เพิ่ม {added} รายการ | ข้าม {skipped} รายการ (SN ซ้ำ)"
    except Exception as e:
        return False, f"❌ Error: {e}"

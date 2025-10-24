
import gspread
import json
from google.oauth2.service_account import Credentials

CONFIG_SHEET = "config"

def get_client_from_env():
    import os
    service_account_info = json.loads(os.getenv("gservice_account", "{}") or "{}")
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    return gspread.authorize(creds)

def ensure_config_ws(sh):
    try:
        ws = sh.worksheet(CONFIG_SHEET)
    except Exception:
        ws = sh.add_worksheet(CONFIG_SHEET, rows=100, cols=3)
        ws.append_row(["key","value","updated_at"])
    return ws

def read_config(sh):
    ws = ensure_config_ws(sh)
    rows = ws.get_all_records()
    data = {}
    for r in rows:
        k = str(r.get("key")).strip()
        v = r.get("value")
        if k:
            data[k] = v
    return data

def write_config(sh, updates: dict, now_iso: str):
    ws = ensure_config_ws(sh)
    rows = ws.get_all_records()
    idx = { str(r.get("key")).strip(): i for i,r in enumerate(rows, start=2) }
    for k,v in updates.items():
        if k in idx:
            row = idx[k]
            ws.update(f"A{row}:C{row}", [[k, str(v), now_iso]])
        else:
            ws.append_row([k, str(v), now_iso])

import json, os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import streamlit as st

def get_client():
    # Intenta secrets (Cloud)
    sa_json = st.secrets.get("gservice_account")
    if sa_json:
        if isinstance(sa_json, str):
            sa_info = json.loads(sa_json)
        else:
            sa_info = sa_json
        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(sa_info, scopes=scope)
        return gspread.authorize(creds)
    # Intento local con service_account.json
    if os.path.exists("service_account.json"):
        scope = ["https://spreadsheets.google.com/feeds",
                 "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scopes=scope)
        return gspread.authorize(creds)
    raise RuntimeError("No se encontraron credenciales (secrets o service_account.json)")

def open_sheet(gc, sheet_id_or_title):
    # Primero intenta por key (ID)
    try:
        return gc.open_by_key(sheet_id_or_title)
    except Exception:
        # Luego por nombre/título
        return gc.open(sheet_id_or_title)

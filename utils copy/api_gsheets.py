# utils/api_gsheets.py
import json
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

def get_client():
    # st.secrets["gservice_account"] puede ser dict (TOML) o JSON string
    sa = st.secrets["gservice_account"]
    sa_info = json.loads(sa) if isinstance(sa, str) else dict(sa)
    creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    return gspread.authorize(creds)

def open_sheet(gc, sheet_id_or_title):
    try:
        return gc.open_by_key(sheet_id_or_title)
    except Exception:
        # fallback por título
        return gc.open(sheet_id_or_title)


import streamlit as st
import os, json, glob
from datetime import datetime
from utils.admin_config import get_client_from_env, read_config, write_config
from google.oauth2.service_account import Credentials
import gspread

st.set_page_config(page_title="FluxFin — Admin", layout="wide")
st.title("🧑‍💻 Panel de Administración — FluxFin Cloud")

allow = st.secrets.get("ADMIN_ALLOWLIST", "")
allowlist = [x.strip().lower() for x in allow.split(",") if x.strip()]
user_hint = st.secrets.get("ADMIN_HINT","")

if allowlist:
    current_user = st.text_input("Identifícate (email o usuario autorizado):", value=user_hint)
    if current_user.strip().lower() not in allowlist:
        st.warning("Acceso restringido. Agrega tu email/usuario a ADMIN_ALLOWLIST en Secrets.")
        st.stop()

SHEET_ID = st.secrets.get("SHEET_ID") or st.text_input("SHEET_ID (solo admins)")

logos = sorted(glob.glob("assets/logos/*.png"))
with open("assets/themes.json","r") as f:
    themes = json.load(f)

col1, col2 = st.columns([2,1])
with col1:
    st.subheader("🎨 Diseños de interfaz (themes)")
    theme_name = st.selectbox("Elegí un theme", list(themes.keys()))
    st.json(themes[theme_name])
with col2:
    st.subheader("☁️ Ícono / Favicon")
    if len(logos)==0:
        st.error("No hay logos en assets/logos")
    else:
        favicon_idx = st.number_input("Elegí índice de logo para favicon", min_value=1, max_value=len(logos), value=1, step=1)
        st.image(logos[favicon_idx-1], caption=f"favicon: {os.path.basename(logos[favicon_idx-1])}", use_container_width=True)

st.subheader("🖼️ Logos disponibles (elige 1 como principal)")
if len(logos)>0:
    sel = st.number_input("Logo principal (índice)", min_value=1, max_value=len(logos), value=1, step=1)
    st.image(logos[sel-1], caption=f"{os.path.basename(logos[sel-1])}", use_container_width=True)

up = st.file_uploader("Subir logo (PNG)", type=["png"])
if up:
    save_path = f"assets/logos/custom_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    with open(save_path,"wb") as f:
        f.write(up.read())
    st.success(f"Logo subido: {save_path}")

st.divider()
st.subheader("💾 Guardar configuración activa")
if SHEET_ID:
    try:
        gc = get_client_from_env()
        sh = gc.open_by_key(SHEET_ID)
        if st.button("Aplicar y guardar (Sheet: config)") and len(logos)>0:
            now_iso = datetime.now().isoformat()
            updates = {
                "selected_theme": theme_name,
                "selected_logo": os.path.basename(logos[sel-1]),
                "selected_favicon": os.path.basename(logos[favicon_idx-1])
            }
            write_config(sh, updates, now_iso)
            st.success("Configuración guardada en la hoja 'config'.")
    except Exception as e:
        st.error(f"No se pudo abrir la Sheet: {e}")
else:
    st.info("Setea SHEET_ID en Secrets para persistir configuración.")

st.divider()
st.subheader("🧪 Modo demo (placeholder)")
st.write("Activación de datos demo llegará en PR de 'Semillas & Tests'.")

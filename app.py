import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import requests

from utils.api_gsheets import get_client, open_sheet

st.set_page_config(page_title="FluxFin — Cloud", layout="wide")
st.title("FluxFin — Finanzas personales (Cloud)")

SHEET_ID = st.secrets.get("SHEET_ID", None) or st.text_input("SHEET_ID (provisorio si estás local):")

@st.cache_resource(show_spinner=False)
def _get_ws_clients(sheet_id):
    gc = get_client()
    sh = open_sheet(gc, sheet_id)
    ws_tx = sh.worksheet("transactions")
    ws_bg = sh.worksheet("budgets")
    ws_ex = sh.worksheet("exchange_rates")
    return sh, ws_tx, ws_bg, ws_ex

def _safe_get_df(ws, expected_cols):
    try:
        data = ws.get_all_records()
        df = pd.DataFrame(data)
        for c in expected_cols:
            if c not in df.columns: df[c] = None
        return df[expected_cols]
    except Exception:
        return pd.DataFrame(columns=expected_cols)

@st.cache_data(ttl=60, show_spinner=False)
def fetch_mep():
    try:
        j = requests.get("https://dolarapi.com/v1/dolares/bolsa", timeout=8).json()
        return dict(venta=j.get("venta"), compra=j.get("compra"), fecha=j.get("fechaActualizacion"))
    except Exception:
        return None

if SHEET_ID:
    try:
        sh, ws_tx, ws_bg, ws_ex = _get_ws_clients(SHEET_ID)
    except Exception as e:
        st.error(f"No se pudo abrir la Google Sheet: {e}")
        st.stop()
else:
    st.info("Colocá el SHEET_ID arriba (si estás local) o configúralo en Secrets en la nube.")
    st.stop()

# Sidebar
mep = fetch_mep()
if mep:
    st.sidebar.metric("Dólar MEP (venta)", mep["venta"])

menu = st.sidebar.radio("Menú", ["Inicio", "Registrar movimiento", "Presupuesto y Consumo", "Exportar"])

if menu == "Inicio":
    st.header("Resumen")
    tx = _safe_get_df(ws_tx, ["fecha","tipo","descripcion","categoria","subcategoria","monto","moneda","medio_pago","proyecto","notas","creado_en"])
    if tx.empty:
        st.info("Sin movimientos aún.")
    else:
        # limpieza y métricas
        with st.spinner("Calculando..."):
            def _to_date(x):
                try: return pd.to_datetime(x)
                except: return pd.NaT
            tx["fecha"] = tx["fecha"].map(_to_date)
            tx["monto"] = pd.to_numeric(tx["monto"], errors="coerce").fillna(0.0)
            tx["signo"] = tx["tipo"].map(lambda t: 1 if str(t).lower()=="ingreso" else -1)
            tx["monto_signed"] = tx["monto"] * tx["signo"]
            saldo = tx["monto_signed"].sum()
        st.metric("Saldo estimado (moneda base)", f"{saldo:,.2f}".replace(",", "."))

        gastos = tx[tx["signo"]<0].groupby("categoria")["monto"].sum().reset_index().sort_values("monto", ascending=False)
        if not gastos.empty:
            fig = px.pie(gastos, names="categoria", values="monto", title="Gastos por categoría (últimos registros)")
            st.plotly_chart(fig, use_container_width=True)
        st.subheader("Últimos movimientos")
        st.dataframe(tx.tail(15), use_container_width=True)

elif menu == "Registrar movimiento":
    st.header("Registrar movimiento")
    with st.form("mov_form"):
        tipo = st.selectbox("Tipo", ["Gasto","Ingreso","Tarjeta / Consumo","Inversión"])
        fecha = st.date_input("Fecha", value=datetime.today())
        descripcion = st.text_input("Descripción")
        categoria = st.selectbox("Categoría", ["Vivienda","Alimentos","Transporte","Salud","Ocio","Inversiones","Otros"])
        subcategoria = st.text_input("Subcategoría (opcional)")
        monto = st.number_input("Monto", min_value=0.0, format="%.2f")
        moneda = st.selectbox("Moneda", ["ARS","USD"])
        medio_pago = st.selectbox("Medio de pago", ["Efectivo","Debito","Tarjeta","Transferencia"])
        proyecto = st.text_input("Proyecto / Tag (opcional)")
        notas = st.text_area("Notas (opcional)")
        ok = st.form_submit_button("Guardar")
        if ok:
            ws_tx.append_row([fecha.isoformat(), tipo, descripcion, categoria, subcategoria,
                              float(monto), moneda, medio_pago, proyecto, notas, datetime.now().isoformat()],
                             value_input_option="USER_ENTERED")
            st.success("Movimiento guardado.")

elif menu == "Presupuesto y Consumo":
    st.header("Presupuesto y Consumo")
    from calendar import month_name
    hoy = datetime.today()
    mes_anno = f"{hoy.strftime('%m')}-{hoy.year}"
    st.caption(f"Mes seleccionado: **{mes_anno}**")

    with st.form("pres_form"):
        cat = st.selectbox("Categoría", ["Vivienda","Alimentos","Transporte","Salud","Ocio","Inversiones","Otros"])
        monto_planeado = st.number_input("Monto planeado", min_value=0.0, format="%.2f")
        if st.form_submit_button("Agregar presupuesto"):
            ws_bg.append_row([mes_anno, cat, float(monto_planeado)], value_input_option="USER_ENTERED")
            st.success("Presupuesto guardado.")

    tx = _safe_get_df(ws_tx, ["fecha","tipo","categoria","monto"])
    bg = _safe_get_df(ws_bg, ["mes_anno","categoria","monto_planeado"])

    if tx.empty or bg.empty:
        st.info("Necesitás al menos un movimiento y un presupuesto para comparar.")
    else:
        tx["fecha"] = pd.to_datetime(tx["fecha"], errors="coerce")
        tx["mes_anno"] = tx["fecha"].dt.strftime("%m-%Y")
        # gastos reales del mes
        gastos_mes = tx[(tx["tipo"]=="Gasto") & (tx["mes_anno"]==mes_anno)].groupby("categoria")["monto"].sum().reset_index()
        comp = bg[bg["mes_anno"]==mes_anno].merge(gastos_mes, on="categoria", how="left").fillna({"monto":0})
        comp["diferencia"] = comp["monto_planeado"] - comp["monto"]
        st.subheader("Comparación")
        st.dataframe(comp, use_container_width=True)
        if not comp.empty:
            fig = px.bar(comp, x="categoria", y=["monto_planeado","monto"], barmode="group", title="Presupuesto vs Gasto")
            st.plotly_chart(fig, use_container_width=True)

elif menu == "Exportar":
    st.header("Exportar datos")
    tx = _safe_get_df(ws_tx, ["fecha","tipo","descripcion","categoria","subcategoria","monto","moneda","medio_pago","proyecto","notas","creado_en"])
    if tx.empty:
        st.info("No hay datos para exportar.")
    else:
        xls = tx.to_excel(index=False)
        st.download_button("Descargar movimientos (xlsx)", data=xls, file_name="movimientos_fluxfin.xlsx")

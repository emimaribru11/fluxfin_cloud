# FluxFin (Cloud)

App de finanzas personales en la nube con Streamlit + Google Sheets.

## Despliegue rápido (Streamlit Cloud)

1. Sube este repo a GitHub.
2. En Streamlit Cloud, crea una app nueva apuntando a `app.py`.
3. En **Settings → Secrets**, agrega:
```
SHEET_ID="REEMPLAZA_CON_TU_ID_DE_SHEET"
gservice_account="PEGA_AQUI_EL_JSON_COMPLETO_DE_TU_SERVICE_ACCOUNT"
```
4. Deploy.

## Local
```
pip install -r requirements.txt
streamlit run app.py
```

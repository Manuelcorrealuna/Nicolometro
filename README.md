# Nicolometro

App MVP en Streamlit + Supabase para registrar la posicion moral de personas y construir rankings.

## 1) Crear proyecto en Supabase
- Crea un proyecto nuevo en https://app.supabase.com
- Espera a que la base de datos este lista.

## 2) Ejecutar schema.sql
- En el panel de Supabase, abre SQL Editor.
- Copia y ejecuta el contenido de `sql/schema.sql`.

## 3) Obtener SUPABASE_URL y SUPABASE_ANON_KEY
- En Supabase: Settings -> API
- Copia la URL del proyecto y el anon public key.

## 4) Configurar secrets en Streamlit Community Cloud
En tu app, abre Settings -> Secrets y agrega:

```
SUPABASE_URL = "https://xxxx.supabase.co"
SUPABASE_ANON_KEY = "tu_anon_key"
ADMIN_MODE = "true"  # opcional
```

## 5) Deploy gratis en Streamlit Community Cloud
- Sube este repo a GitHub.
- En https://share.streamlit.io crea una nueva app y selecciona el repo.
- Define `app.py` como archivo principal.
- Agrega los secrets y despliega.

## Ejecutar localmente

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

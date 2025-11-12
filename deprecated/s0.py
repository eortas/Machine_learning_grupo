import streamlit as st
import os
import re
import pandas as pd
from datetime import datetime
from git import Repo

# === Configuración del capítulo ===
CAPITULO = "Capítulo 1"
COLUMNA = "Capítulo 1"
CARPETA_DESTINO = "capitulo_01"
FECHA_LIMITE = datetime(2025, 11, 9)

REPO_URL = "https://github.com/eortas/Machine_learning_secta.git"
REPO_DIR = "repo_temp"
TOKEN = st.secrets["GITHUB_TOKEN"]
REGISTRO_PATH = os.path.join(REPO_DIR, "uploads", "registro_entregas.csv")

# === Configuración visual ===
st.set_page_config(layout="centered", page_title="Entregas ML secta post bootcamp")
st.markdown("""<style>
.stApp {
    background-image: url('https://i.ibb.co/bgYRvLST/fondo-ml.jpg');
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    color: #000;
}
.center-content {
    margin-left: auto;
    margin-right: auto;
    max-width: 800px;
    padding: 20px;
    background-color: rgba(255,255,255,0.4);
    border-radius: 10px;
    box-shadow: 0 0 15px rgba(0,0,0,0.3);
    overflow-wrap: break-word;
    color: #000;
}
body, h1, h2, h3, h4, h5, h6, p, label, span, div {
    color: #000 !important;
}
[data-testid="stTable"], [data-testid="stDataFrame"] {
    background-color: #fff !important;
    color: #000 !important;
    border-radius: 8px;
    padding: 10px;
}
@media screen and (max-width: 768px) {
    .center-content {
        max-width: 95%;
        padding: 15px;
        border-radius: 8px;
        box-shadow: none;
    }
    .stApp {
        background-size: cover;
        background-position: center top;
    }
    .center-content table {
        display: block;
        overflow-x: auto;
        width: 100%;
    }
    .center-content td, .center-content th {
        word-break: break-word;
    }
}
@media screen and (max-width: 1366px) {
    .center-content {
        max-width: 95%;
        font-size: 15px;
        padding: 15px;
        box-shadow: none;
    }
    [data-testid="stTable"], [data-testid="stDataFrame"] {
        overflow-x: auto;
        max-width: 100%;
        background-color: #fff !important;
        color: #000 !important;
        border-radius: 8px;
        padding: 10px;
    }
    .animal-left, .animal-right {
        display: none;
    }
    h1, h2, h3, p, label, span, div {
        font-size: 15px !important;
    }
}
</style>""", unsafe_allow_html=True)

# === Fecha límite ===
hoy = datetime.now()
dias_restantes = (FECHA_LIMITE - hoy).days

st.title(f"Subida de prácticas - {CAPITULO}")
if dias_restantes > 1:
    st.info(f"Quedan **{dias_restantes} días** para entregar la práctica.")
elif dias_restantes == 1:
    st.warning("⚠️ ¡Mañana es el último día para entregar la práctica!")
elif dias_restantes == 0:
    st.error("🚨 La entrega cierra hoy. Se aceptarán archivos solo hasta medianoche.")
else:
    st.error("❌ El plazo de entrega ha finalizado. No se pueden subir más archivos.")
    st.stop()

st.caption(f"Fecha límite: {FECHA_LIMITE.strftime('%d/%m/%Y')}")

# === Clonación o actualización del repositorio ===
if not os.path.exists(REPO_DIR):
    Repo.clone_from(f"https://{TOKEN}@github.com/eortas/Machine_learning_secta.git", REPO_DIR)
repo = Repo(REPO_DIR)
repo.remote(name="origin").pull()

# === Carga del registro ===
if os.path.exists(REGISTRO_PATH):
    df = pd.read_csv(REGISTRO_PATH, encoding="utf-8")
else:
    st.error("No se encuentra el archivo registro_entregas.csv en el repositorio.")
    st.stop()

if COLUMNA not in df.columns:
    df[COLUMNA] = ""

# === Tabla de entregas ===
st.subheader("Listado de miembros y estado de entregas")
df_show = df.copy().fillna("❌")
st.dataframe(df_show, use_container_width=True)

# === Estado de subida ===
if "archivo_subido" not in st.session_state:
    st.session_state.archivo_subido = False
    st.session_state.archivo_nombre = ""
    st.session_state.archivo_autor = ""

# === Subida de archivo ===
if "archivo_guardado" not in st.session_state:
    st.session_state.archivo_guardado = False

archivo = st.file_uploader(
    "Sube tu archivo .zip. Recuerda usar el formato capX-nombre.zip (ej. cap1-pepe.zip)",
    type=["zip"],
    key="uploader"
)

if archivo and not st.session_state.archivo_guardado:
    patron = r"^(cap\d{1,2})-([a-zA-Z0-9_]+)\.zip$"
    match = re.match(patron, archivo.name)

    if not match:
        st.error("❌ Nombre de archivo no válido. Usa el formato: capX-nombre.zip (ej. cap5-pepe.zip)")
        st.stop()

    capitulo_archivo, nombre = match.groups()
    nombre = nombre.lower()

    nombres_validos = [n.lower() for n in df["Nombre"].values]
    if nombre not in nombres_validos:
        st.error(f"El nombre '{nombre}' no está en la lista de miembros válidos.")
        st.stop()

    carpeta_capitulo = os.path.join(REPO_DIR, "uploads", CARPETA_DESTINO)
    os.makedirs(carpeta_capitulo, exist_ok=True)
    fecha = hoy.strftime("%Y-%m-%d")
    filepath = os.path.join(carpeta_capitulo, archivo.name)
    with open(filepath, "wb") as f:
        f.write(archivo.getbuffer())

    df.loc[df["Nombre"].str.lower() == nombre, COLUMNA] = "✅"
    df.to_csv(REGISTRO_PATH, index=False)

    repo.git.add(".")
    repo.index.commit(f"{CAPITULO} - Subida de {nombre} ({fecha})")
    origin = repo.remote(name="origin")
    origin.push()

    st.session_state.archivo_guardado = True
    st.session_state.archivo_nombre = archivo.name
    st.session_state.archivo_autor = nombre

# === Mensaje de éxito ===
if st.session_state.archivo_guardado:
    st.markdown(f"""
    🎉 **Entrega recibida:** `{st.session_state.archivo_nombre}`  
    👤 **Autor:** `{st.session_state.archivo_autor}`  
    ✅ Registro actualizado.  
    🙌 Eres un buen miembro de nuestra ~~secta~~ comunidad. ¡Sigue así!
    """, unsafe_allow_html=True)

    if st.button("¿Quieres subir otro archivo?"):
        for key in ["archivo_guardado", "archivo_nombre", "archivo_autor"]:
            st.session_state[key] = None
        st.experimental_rerun()

# === Mensaje de éxito ===
if st.session_state.archivo_subido:
    st.markdown(f"""
    🎉 **Entrega recibida:** `{st.session_state.archivo_nombre}`  
    👤 **Autor:** `{st.session_state.archivo_autor}`  
    ✅ Registro actualizado.  
    🙌 Eres un buen miembro de nuestra ~~secta~~ comunidad. ¡Sigue así!
    """, unsafe_allow_html=True)

    if st.button("¿Quieres subir otro archivo?"):
        st.session_state.archivo_subido = False
        st.session_state.archivo_nombre = ""
        st.session_state.archivo_autor = ""
        st.rerun()
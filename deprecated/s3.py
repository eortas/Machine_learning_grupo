import streamlit as st
import os
import re
import pandas as pd
import zipfile
import json
from datetime import datetime
from git import Repo
from difflib import SequenceMatcher
import urllib.request
import ssl


# === Configuración del capítulo ===
CAPITULO = "Capítulo 2"
COLUMNA = "Capítulo 2"
CARPETA_DESTINO = "capitulo_02"
FECHA_LIMITE = datetime(2025, 11, 9)

REPO_URL = "https://github.com/eortas/Machine_learning_secta.git"
REPO_DIR = "repo_temp"
TOKEN = st.secrets["GITHUB_TOKEN"]
REGISTRO_PATH = os.path.join(REPO_DIR, "uploads", "registro_entregas.csv")

# URL del notebook oficial
SOLUCION_OFICIAL_URL = "https://github.com/ageron/handson-ml3/raw/main/02_end_to_end_machine_learning_project.ipynb"


# === Evaluación de originalidad ===
def evaluar_originalidad(contenido_usuario, contenido_oficial, nombre, capitulo, fecha):
    """
    Compara directamente el contenido JSON completo de ambos notebooks
    """
    # Convertir los diccionarios a strings JSON para comparar
    str_usuario = json.dumps(contenido_usuario, sort_keys=True)
    str_oficial = json.dumps(contenido_oficial, sort_keys=True)
    
    # Calcular similitud textual directa
    sim_textual = SequenceMatcher(None, str_usuario, str_oficial).ratio()
    
    # Determinar originalidad basado solo en la similitud textual
    if sim_textual > 0.95:
        originalidad = "Copia directa"
    elif sim_textual > 0.85:
        originalidad = "Copia modificada"
    elif sim_textual > 0.7:
        originalidad = "Inspirado"
    else:
        originalidad = "Original"
    
    # Guardar en CSV
    fila = {
        "Nombre": nombre,
        "Capítulo": capitulo,
        "Originalidad": originalidad,
        "Similitud": round(sim_textual, 3),
        "Fecha": fecha
    }
    
    try:
        df_eval = pd.read_csv("evaluacion_originalidad.csv")
        df_eval = pd.concat([df_eval, pd.DataFrame([fila])], ignore_index=True)
    except:
        df_eval = pd.DataFrame([fila])
    
    df_eval.to_csv("evaluacion_originalidad.csv", index=False)
    
    return originalidad, sim_textual


# === Hall of Fame ===
def generar_hall_of_fame(capitulo):
    try:
        df_eval = pd.read_csv("evaluacion_originalidad.csv")
    except FileNotFoundError:
        return {}
    
    df_cap = df_eval[df_eval["Capítulo"] == capitulo]
    # Excluir copias directas y modificadas
    df_cap = df_cap[~df_cap["Originalidad"].isin(["Copia directa", "Copia modificada"])]
    
    if df_cap.empty or len(df_cap["Nombre"].unique()) < 3:
        return {}
    
    # Puntuación basada en ORIGINALIDAD (menor similitud = mejor)
    df_cap["Puntuacion"] = 1 - df_cap["Similitud"]
    
    # Ordenar por puntuación (más original primero)
    df_cap = df_cap.sort_values(by="Puntuacion", ascending=False)
    
    # Asignar premios
    nombres_unicos = df_cap["Nombre"].unique()
    
    if len(nombres_unicos) < 3:
        return {}
    
    ganador = df_cap.iloc[0]["Nombre"].lower()
    creativo = df_cap[df_cap["Nombre"] != df_cap.iloc[0]["Nombre"]].iloc[0]["Nombre"].lower()
    explicativo = df_cap[~df_cap["Nombre"].isin([df_cap.iloc[0]["Nombre"], 
                                                   df_cap[df_cap["Nombre"] != df_cap.iloc[0]["Nombre"]].iloc[0]["Nombre"]])].iloc[0]["Nombre"].lower()
    
    return {
        "mejor": ganador,
        "creativo": creativo,
        "explicativo": explicativo
    }


# === Función para descargar notebook oficial ===
def descargar_notebook_oficial(url):
    """
    Descarga el notebook oficial desde GitHub sin mostrar mensajes
    """
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    urls_alternativas = [
        url,
        "https://raw.githubusercontent.com/ageron/handson-ml3/main/02_end_to_end_machine_learning_project.ipynb",
    ]
    
    for url_intento in urls_alternativas:
        try:
            req = urllib.request.Request(
                url_intento,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            
            with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                contenido = response.read()
                
                try:
                    contenido_str = contenido.decode("utf-8")
                except:
                    contenido_str = contenido.decode("latin-1")
                
                notebook = json.loads(contenido_str)
                return notebook
                
        except:
            continue
    
    return None


# === Configuración visual ===
st.set_page_config(layout="centered", page_title="Entregas ML secta post bootcamp")

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

# === Estado de subida ===
if "archivo_guardado" not in st.session_state:
    st.session_state.archivo_guardado = False
    st.session_state.archivo_nombre = ""
    st.session_state.archivo_autor = ""
    st.session_state.similitud = 0

# === Subida de archivo ===
archivo = st.file_uploader(
    "Sube tu archivo .zip. Recuerda usar el formato capX-nombre.zip (ej. cap2-pepe.zip)",
    type=["zip"],
    key="uploader"
)

if archivo and not st.session_state.archivo_guardado:
    patron = r"^(cap\d{1,2})-([a-zA-Z0-9_]+)\.zip$"
    match = re.match(patron, archivo.name)
    
    if not match:
        st.error("❌ Nombre de archivo no válido. Usa el formato: capX-nombre.zip (ej. cap2-pepe.zip)")
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

    # === Procesar archivo con spinner ===
    with st.spinner("🔍 Procesando y evaluando tu entrega..."):
        # Extraer notebook del usuario
        notebook_usuario = None
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            archivos_ipynb = [f for f in zip_ref.namelist() if f.endswith(".ipynb") and not f.startswith("__MACOSX")]
            
            if not archivos_ipynb:
                st.error("❌ El archivo .zip no contiene ningún notebook (.ipynb).")
                st.stop()
            
            notebook_file = archivos_ipynb[0]
            
            with zip_ref.open(notebook_file) as f:
                try:
                    notebook_usuario = json.load(f)
                except json.JSONDecodeError as e:
                    st.error(f"❌ El notebook no tiene un formato JSON válido: {e}")
                    st.stop()
                except Exception as e:
                    st.error(f"❌ Error al leer el notebook: {e}")
                    st.stop()

        if not notebook_usuario:
            st.error("❌ No se pudo cargar el notebook del usuario.")
            st.stop()

        # Descargar notebook oficial
        notebook_oficial = descargar_notebook_oficial(SOLUCION_OFICIAL_URL)
        
        if not notebook_oficial:
            st.error("❌ No se pudo descargar el notebook oficial.")
            st.error("Por favor, contacta al administrador del sistema.")
            st.stop()

        # Comparar notebooks
        originalidad, similitud = evaluar_originalidad(
            notebook_usuario, 
            notebook_oficial, 
            nombre, 
            CAPITULO, 
            fecha
        )
        
        st.session_state.similitud = similitud

    # === Mostrar resultado de la comparación ===
    if originalidad == "Copia directa":
        st.error(f"🚫 **COPIA DIRECTA DETECTADA** (Similitud: {similitud*100:.1f}%)")
        st.warning("Tu notebook es prácticamente idéntico al oficial. No recibirás premios.")
    elif originalidad == "Copia modificada":
        st.warning(f"⚠️ **Copia con modificaciones** (Similitud: {similitud*100:.1f}%)")
        st.info("Tu notebook es muy similar al oficial. No recibirás premios.")
    elif originalidad == "Inspirado":
        st.info(f"💡 **Trabajo inspirado** (Similitud: {similitud*100:.1f}%)")
        st.success("Tu trabajo está inspirado en la solución oficial, pero tiene elementos propios.")
    else:
        st.success(f"🎉 **Trabajo original** (Similitud: {similitud*100:.1f}%)")
        st.balloons()
        st.info("¡Felicidades! Eres elegible para premios.")

    # === Actualizar registro ===
    df.loc[df["Nombre"].str.lower() == nombre, COLUMNA] = "✅"
    df.to_csv(REGISTRO_PATH, index=False)

    # === Commit y push ===
    repo.git.add(".")
    repo.index.commit(f"{CAPITULO} - Subida de {nombre} ({fecha})")
    origin = repo.remote(name="origin")
    origin.push()

    st.session_state.archivo_guardado = True
    st.session_state.archivo_nombre = archivo.name
    st.session_state.archivo_autor = nombre

# === Hall of Fame ===
hall = generar_hall_of_fame(COLUMNA)

def marcar_entrega(nombre, estado):
    nombre = nombre.lower()
    if estado == "✅":
        if hall.get("mejor") == nombre:
            return "🏆"
        elif hall.get("creativo") == nombre:
            return "🎨"
        elif hall.get("explicativo") == nombre:
            return "📝"
        else:
            return "✅"
    return "❌"

df_show = df.copy().fillna("❌")
df_show[COLUMNA] = df_show.apply(lambda row: marcar_entrega(row["Nombre"], row[COLUMNA]), axis=1)

# === Tabla de entregas ===
st.subheader("Listado de miembros y estado de entregas")
st.dataframe(df_show, use_container_width=True)

# === Leyenda explicativa ===
with st.expander("📘 ¿Qué significan los emojis en la tabla?"):
    st.markdown("""
    - 🏆 **Mejor entrega**: La entrega más original y completa.  
    - 🎨 **Mención creativa**: Segunda entrega más original.  
    - 📝 **Mención explicativa**: Tercera entrega más original.  
    - ✅ **Entrega válida**: Subida correcta, pero sin mención especial.  
    - ❌ **No entregado**: El miembro no ha subido la práctica.
    
    **Nota**: Las copias directas o modificadas no son elegibles para premios.
    """)

# === Mensaje de éxito ===
if st.session_state.archivo_guardado:
    st.markdown("---")
    st.markdown(f"""
    ### 🎉 Entrega completada
    
    - **Archivo:** `{st.session_state.archivo_nombre}`  
    - **Autor:** `{st.session_state.archivo_autor}`  
    - **Similitud con el original:** `{st.session_state.similitud*100:.1f}%`
    - **Estado:** ✅ Registro actualizado
    
    🙌 ¡Gracias por tu participación en nuestra ~~secta~~ comunidad!
    """)

    if st.button("¿Quieres subir otro archivo?"):
        for key in ["archivo_guardado", "archivo_nombre", "archivo_autor", "similitud"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
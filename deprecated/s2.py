import streamlit as st
import os
import re
import pandas as pd
import zipfile
import json
from datetime import datetime
from git import Repo
import ast
from difflib import SequenceMatcher
import urllib.request


# === Configuración del capítulo ===
CAPITULO = "Capítulo 2"
COLUMNA = "Capítulo 2"
CARPETA_DESTINO = "capitulo_02"
FECHA_LIMITE = datetime(2025, 11, 9)

REPO_URL = "https://github.com/eortas/Machine_learning_secta.git"
REPO_DIR = "repo_temp"
TOKEN = st.secrets["GITHUB_TOKEN"]
REGISTRO_PATH = os.path.join(REPO_DIR, "uploads", "registro_entregas.csv")
SOLUCION_OFICIAL_URL = "https://raw.githubusercontent.com/ageron/handson-ml3/main/02_end_to_end_machine_learning_project.ipynb"


# === Evaluación de originalidad ===
def evaluar_originalidad(codigo_usuario, codigo_oficial, nombre, capitulo, fecha):
    sim_textual = SequenceMatcher(None, codigo_usuario, codigo_oficial).ratio()
    try:
        tree_usuario = ast.dump(ast.parse(codigo_usuario))
        tree_oficial = ast.dump(ast.parse(codigo_oficial))
        sim_estructural = SequenceMatcher(None, tree_usuario, tree_oficial).ratio()
    except:
        sim_estructural = 0.0
    
    sim_semantica = "idéntico" if "fit(" in codigo_usuario and "fit(" in codigo_oficial else "diferente"
    
    # ✅ Umbral más estricto para detectar copias directas
    if sim_textual > 0.95 and sim_estructural > 0.95:
        originalidad = "Copia directa"
    elif sim_textual > 0.7 or sim_estructural > 0.8:
        originalidad = "Inspirado"
    else:
        originalidad = "Original"
    
    fila = {
        "Nombre": nombre,
        "Capítulo": capitulo,
        "Originalidad": originalidad,
        "Sim_textual": round(sim_textual, 3),
        "Sim_estructural": round(sim_estructural, 3),
        "Sim_semantica": sim_semantica,
        "Fecha": fecha
    }
    
    try:
        df_eval = pd.read_csv("evaluacion_originalidad.csv")
        df_eval = pd.concat([df_eval, pd.DataFrame([fila])], ignore_index=True)
    except:
        df_eval = pd.DataFrame([fila])
    
    df_eval.to_csv("evaluacion_originalidad.csv", index=False)
    return originalidad


# === Hall of Fame ===
def generar_hall_of_fame(capitulo):
    try:
        df_eval = pd.read_csv("evaluacion_originalidad.csv")
    except FileNotFoundError:
        return {}
    
    df_cap = df_eval[df_eval["Capítulo"] == capitulo]
    df_cap = df_cap[df_cap["Originalidad"] != "Copia directa"]
    
    if df_cap.empty or len(df_cap["Nombre"].unique()) < 3:
        return {}
    
    # ✅ CORREGIDO: Puntuación basada en ORIGINALIDAD (1 - similitud)
    # Cuanto MÁS diferente del original, MEJOR puntuación
    df_cap["Puntuacion"] = (1 - df_cap["Sim_textual"]) * 0.4 + \
                           (1 - df_cap["Sim_estructural"]) * 0.4 + \
                           df_cap["Sim_semantica"].apply(lambda x: 1 if x == "diferente" else 0) * 0.2
    
    # Mejor entrega: mayor puntuación de originalidad
    df_cap = df_cap.sort_values(by="Puntuacion", ascending=False)
    ganador = df_cap.iloc[0]
    
    # ✅ CORREGIDO: Creativo = menor similitud estructural (más diferente)
    restantes = df_cap[df_cap["Nombre"] != ganador["Nombre"]]
    creativo = restantes.sort_values(by="Sim_estructural", ascending=True).iloc[0]
    
    # Explicativo: el siguiente más original de los restantes
    explicativo = restantes[restantes["Nombre"] != creativo["Nombre"]].sort_values(by="Puntuacion", ascending=False).iloc[0]
    
    return {
        "mejor": ganador["Nombre"].lower(),
        "creativo": creativo["Nombre"].lower(),
        "explicativo": explicativo["Nombre"].lower()
    }


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

    # === Evaluación de originalidad ===
    codigo_usuario = None
    with zipfile.ZipFile(filepath, 'r') as zip_ref:
        for file in zip_ref.namelist():
            if file.endswith(".ipynb"):
                zip_ref.extract(file, "temp_notebook")
                path_usuario = os.path.join("temp_notebook", file)

                try:
                    with open(path_usuario, "r", encoding="utf-8") as f:
                        nb_usuario = json.load(f)
                    codigo_usuario = "\n".join([
                        "".join(cell["source"]) for cell in nb_usuario["cells"] if cell["cell_type"] == "code"
                    ])
                    break
                except Exception as e:
                    st.error(f"❌ Error al leer el notebook del usuario: {e}")
                    st.stop()

    if not codigo_usuario:
        st.error("❌ El archivo .zip no contiene ningún notebook (.ipynb) válido.")
        st.stop()

    def cargar_notebook_remoto(url):
        response = urllib.request.urlopen(url)
        contenido = response.read().decode("utf-8")
        return json.loads(contenido)

    try:
        nb_oficial = cargar_notebook_remoto(SOLUCION_OFICIAL_URL)
        codigo_oficial = "\n".join([
            "".join(cell["source"]) for cell in nb_oficial["cells"] if cell["cell_type"] == "code"
        ])
    except Exception as e:
        st.error(f"❌ Error al cargar el notebook oficial desde GitHub: {e}")
        st.stop()

    originalidad = evaluar_originalidad(codigo_usuario, codigo_oficial, nombre, CAPITULO, fecha)

    # ✅ Mostrar advertencia si es copia directa
    if originalidad == "Copia directa":
        st.warning("⚠️ Se ha detectado que tu entrega es una copia directa del notebook oficial. No recibirás premios.")

    df.loc[df["Nombre"].str.lower() == nombre, COLUMNA] = "✅"
    df.to_csv(REGISTRO_PATH, index=False)

    repo.git.add(".")
    repo.index.commit(f"{CAPITULO} - Subida de {nombre} ({fecha})")
    origin = repo.remote(name="origin")
    origin.push()

    st.session_state.archivo_guardado = True
    st.session_state.archivo_nombre = archivo.name
    st.session_state.archivo_autor = nombre

# === Hall of Fame actual ===
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
    - 🏆 **Mejor entrega**: Resolución técnica impecable, completa y original.  
    - 🎨 **Mención creativa**: Enfoque visual o narrativo destacado.  
    - 📝 **Mención explicativa**: Markdown claro, bien estructurado y pedagógico.  
    - ✅ **Entrega válida**: Subida correcta, pero sin mención especial.  
    - ❌ **No entregado**: El miembro no ha subido la práctica.
    """)

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
        st.rerun()  # ✅ Corregido: st.rerun() en lugar de st.experimental_rerun()
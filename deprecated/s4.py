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
import requests


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

# Se puede elegir entre groq u otras APIs
API_EVALUACION = "groq"  

# API Keys (añadir a secrets.toml y poner en .gitignore)

try:
    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
    GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
except:
    GROQ_API_KEY = ""
    GEMINI_API_KEY = ""


# === Enunciado del ejercicio ===
ENUNCIADO_EJERCICIO = """
**Ejercicio: End-to-End Machine Learning Project**

El objetivo de este capítulo es construir un modelo de Machine Learning completo para predecir precios de viviendas en California.

**Tareas a realizar:**

1. **Exploración de datos:**
   - Cargar el dataset de viviendas de California
   - Analizar las características principales
   - Visualizar distribuciones y correlaciones
   - Identificar valores faltantes y outliers

2. **Preprocesamiento:**
   - Dividir datos en train/test
   - Crear un pipeline de transformación
   - Manejar valores faltantes
   - Escalar características numéricas
   - Codificar variables categóricas

3. **Modelado:**
   - Entrenar al menos 2 modelos diferentes
   - Usar validación cruzada
   - Optimizar hiperparámetros (opcional)
   - Evaluar con métricas apropiadas (RMSE, MAE)

4. **Análisis de resultados:**
   - Comparar modelos
   - Analizar errores
   - Visualizar predicciones vs valores reales
   - Documentar conclusiones

**Criterios de evaluación (sobre 10):**
- Exploración de datos completa (2 puntos)
- Preprocesamiento correcto (2 puntos)
- Implementación de modelos (3 puntos)
- Evaluación y análisis (2 puntos)
- Documentación y claridad (1 punto)
"""


# === Función para extraer contenido del notebook ===
def extraer_contenido_notebook(notebook):
    """
    Extrae código y markdown de un notebook
    """
    codigo = []
    markdown = []
    
    for cell in notebook.get("cells", []):
        cell_type = cell.get("cell_type", "")
        source = cell.get("source", [])
        
        if isinstance(source, list):
            source_text = "".join(source)
        else:
            source_text = source
        
        if cell_type == "code":
            codigo.append(source_text)
        elif cell_type == "markdown":
            markdown.append(source_text)
    
    return {
        "codigo": "\n\n".join(codigo),
        "markdown": "\n\n".join(markdown)
    }


# === Evaluación con Groq  ===
def evaluar_con_groq(notebook_usuario):
   
    if not GROQ_API_KEY:
        return None
    
    contenido = extraer_contenido_notebook(notebook_usuario)
    
    # Limitar contenido para no exceder tokens, optimizado para Groq
    # ~1,500 tokens de código + ~500 tokens markdown = ~2,000 tokens del alumno
    # + ~1,000 tokens de prompt/enunciado = ~3,000 tokens total
    codigo = contenido["codigo"][:6000]  # ~1,500 tokens
    markdown = contenido["markdown"][:2000]  # ~500 tokens
    
    prompt = f"""Eres un profesor experto en Machine Learning evaluando la práctica de un estudiante.

**ENUNCIADO DEL EJERCICIO:**
{ENUNCIADO_EJERCICIO}

**NOTEBOOK DEL ESTUDIANTE:**

CÓDIGO:
```python
{codigo}
```

EXPLICACIONES (MARKDOWN):
{markdown}

**INSTRUCCIONES DE EVALUACIÓN:**

Evalúa el notebook del estudiante con una nota de 0 a 10 basándote en:
1. Exploración de datos (0-2 puntos)
2. Preprocesamiento (0-2 puntos)
3. Modelos implementados (0-3 puntos)
4. Evaluación y análisis (0-2 puntos)
5. Documentación (0-1 punto)

Devuelve tu respuesta en este formato JSON exacto:
{{
    "nota_total": <número del 0 al 10 con un decimal>,
    "exploracion": <puntos de 0 a 2>,
    "preprocesamiento": <puntos de 0 a 2>,
    "modelos": <puntos de 0 a 3>,
    "evaluacion": <puntos de 0 a 2>,
    "documentacion": <puntos de 0 a 1>,
    "comentario": "<breve comentario de 2-3 líneas>",
    "puntos_fuertes": ["<punto 1>", "<punto 2>"],
    "areas_mejora": ["<área 1>", "<área 2>"]
}}

Sé justo pero exigente. Solo da puntuación completa si el trabajo es excelente."""

    try:
        # Intentar hasta 3 veces con espera incremental (por si hay rate limit)
        max_intentos = 3
        
        for intento in range(max_intentos):
            try:
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",  # Modelo gratuito muy bueno
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 1000
                    },
                    timeout=60
                )
                
                if response.status_code == 200:
                    resultado = response.json()
                    contenido_respuesta = resultado["choices"][0]["message"]["content"]
                    
                    # Extraer JSON de la respuesta
                    inicio = contenido_respuesta.find('{')
                    fin = contenido_respuesta.rfind('}') + 1
                    
                    if inicio != -1 and fin > inicio:
                        json_str = contenido_respuesta[inicio:fin]
                        evaluacion = json.loads(json_str)
                        return evaluacion
                
                # Si hay rate limit (429), esperar y reintentar
                elif response.status_code == 429:
                    if intento < max_intentos - 1:
                        import time
                        tiempo_espera = (intento + 1) * 30  # 30s, 60s, 90s
                        time.sleep(tiempo_espera)
                        continue
                    else:
                        return None
                else:
                    return None
                    
            except requests.exceptions.Timeout:
                if intento < max_intentos - 1:
                    continue
                return None
        
        return None
        
    except Exception as e:
        st.warning(f"Error con Groq: {e}")
        return None


# === Evaluación con Google Gemini (GRATIS) ===
def evaluar_con_gemini(notebook_usuario):
    """
    Usa Google Gemini API (gratis hasta 15 req/min) para evaluar el notebook
    """
    if not GEMINI_API_KEY:
        return None
    
    contenido = extraer_contenido_notebook(notebook_usuario)
    
    # Limitar contenido (Gemini tiene más margen pero lo limitamos igual)
    codigo = contenido["codigo"][:6000]  # ~1,500 tokens
    markdown = contenido["markdown"][:2000]  # ~500 tokens
    
    prompt = f"""Eres un profesor experto en Machine Learning evaluando la práctica de un estudiante.

**ENUNCIADO DEL EJERCICIO:**
{ENUNCIADO_EJERCICIO}

**NOTEBOOK DEL ESTUDIANTE:**

CÓDIGO:
```python
{codigo}
```

EXPLICACIONES (MARKDOWN):
{markdown}

**INSTRUCCIONES DE EVALUACIÓN:**

Evalúa el notebook del estudiante con una nota de 0 a 10 basándote en:
1. Exploración de datos (0-2 puntos)
2. Preprocesamiento (0-2 puntos)
3. Modelos implementados (0-3 puntos)
4. Evaluación y análisis (0-2 puntos)
5. Documentación (0-1 punto)

Devuelve tu respuesta en este formato JSON exacto:
{{
    "nota_total": <número del 0 al 10 con un decimal>,
    "exploracion": <puntos de 0 a 2>,
    "preprocesamiento": <puntos de 0 a 2>,
    "modelos": <puntos de 0 a 3>,
    "evaluacion": <puntos de 0 a 2>,
    "documentacion": <puntos de 0 a 1>,
    "comentario": "<breve comentario de 2-3 líneas>",
    "puntos_fuertes": ["<punto 1>", "<punto 2>"],
    "areas_mejora": ["<área 1>", "<área 2>"]
}}

Sé justo pero exigente."""

    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 1000
                }
            },
            timeout=30
        )
        
        if response.status_code == 200:
            resultado = response.json()
            contenido_respuesta = resultado["candidates"][0]["content"]["parts"][0]["text"]
            
            # Extraer JSON
            inicio = contenido_respuesta.find('{')
            fin = contenido_respuesta.rfind('}') + 1
            
            if inicio != -1 and fin > inicio:
                json_str = contenido_respuesta[inicio:fin]
                evaluacion = json.loads(json_str)
                return evaluacion
        
        return None
        
    except Exception as e:
        st.warning(f"Error con Gemini: {e}")
        return None


# === Evaluación principal ===
def evaluar_respuestas_ia(notebook_usuario):
    """
    Evalúa el notebook usando IA gratuita
    """
    # Intentar con la API configurada
    if API_EVALUACION == "groq":
        evaluacion = evaluar_con_groq(notebook_usuario)
        if evaluacion:
            return evaluacion
        # Fallback a Gemini si falla Groq
        evaluacion = evaluar_con_gemini(notebook_usuario)
        if evaluacion:
            return evaluacion
    elif API_EVALUACION == "gemini":
        evaluacion = evaluar_con_gemini(notebook_usuario)
        if evaluacion:
            return evaluacion
        # Fallback a Groq si falla Gemini
        evaluacion = evaluar_con_groq(notebook_usuario)
        if evaluacion:
            return evaluacion
    
    # Si ambas fallan, retornar evaluación por defecto
    return {
        "nota_total": 5.0,
        "exploracion": 1.0,
        "preprocesamiento": 1.0,
        "modelos": 1.5,
        "evaluacion": 1.0,
        "documentacion": 0.5,
        "comentario": "No se pudo evaluar automáticamente. Revisión manual necesaria.",
        "puntos_fuertes": ["Archivo subido correctamente"],
        "areas_mejora": ["Requiere revisión manual"]
    }


# === Evaluación de originalidad ===
def evaluar_originalidad(contenido_usuario, contenido_oficial):
    """
    Compara directamente el contenido JSON completo de ambos notebooks
    """
    str_usuario = json.dumps(contenido_usuario, sort_keys=True)
    str_oficial = json.dumps(contenido_oficial, sort_keys=True)
    
    sim_textual = SequenceMatcher(None, str_usuario, str_oficial).ratio()
    
    if sim_textual > 0.95:
        originalidad = "Copia directa"
    elif sim_textual > 0.85:
        originalidad = "Copia modificada"
    elif sim_textual > 0.7:
        originalidad = "Inspirado"
    else:
        originalidad = "Original"
    
    return originalidad, sim_textual


# === Guardar evaluación completa ===
def guardar_evaluacion(nombre, capitulo, fecha, originalidad, similitud, evaluacion_ia):
    """
    Guarda toda la información de la evaluación en el CSV
    """
    fila = {
        "Nombre": nombre,
        "Capítulo": capitulo,
        "Originalidad": originalidad,
        "Similitud": round(similitud, 3),
        "Nota_Total": evaluacion_ia["nota_total"],
        "Exploracion": evaluacion_ia["exploracion"],
        "Preprocesamiento": evaluacion_ia["preprocesamiento"],
        "Modelos": evaluacion_ia["modelos"],
        "Evaluacion": evaluacion_ia["evaluacion"],
        "Documentacion": evaluacion_ia["documentacion"],
        "Comentario": evaluacion_ia["comentario"],
        "Fecha": fecha
    }
    
    try:
        df_eval = pd.read_csv("evaluacion_originalidad.csv")
        df_eval = pd.concat([df_eval, pd.DataFrame([fila])], ignore_index=True)
    except:
        df_eval = pd.DataFrame([fila])
    
    df_eval.to_csv("evaluacion_originalidad.csv", index=False)


# === Hall of Fame ===
def generar_hall_of_fame(capitulo):
    try:
        df_eval = pd.read_csv("evaluacion_originalidad.csv")
    except FileNotFoundError:
        return {}
    
    df_cap = df_eval[df_eval["Capítulo"] == capitulo]
    df_cap = df_cap[~df_cap["Originalidad"].isin(["Copia directa", "Copia modificada"])]
    
    if df_cap.empty or len(df_cap["Nombre"].unique()) < 3:
        return {}
    
    # Puntuación combinada: originalidad (30%) + nota IA (70%)
    df_cap["Puntuacion_Combinada"] = (1 - df_cap["Similitud"]) * 0.3 + (df_cap["Nota_Total"] / 10) * 0.7
    
    df_cap = df_cap.sort_values(by="Puntuacion_Combinada", ascending=False)
    
    nombres_unicos = df_cap["Nombre"].unique()
    
    if len(nombres_unicos) < 3:
        return {}
    
    ganador = df_cap.iloc[0]["Nombre"].lower()
    
    df_creativo = df_cap[df_cap["Nombre"] != df_cap.iloc[0]["Nombre"]].sort_values(by="Similitud", ascending=True)
    creativo = df_creativo.iloc[0]["Nombre"].lower() if len(df_creativo) > 0 else None
    
    df_explicativo = df_cap[~df_cap["Nombre"].isin([df_cap.iloc[0]["Nombre"], creativo])]
    if len(df_explicativo) > 0:
        df_explicativo = df_explicativo.sort_values(by="Documentacion", ascending=False)
        explicativo = df_explicativo.iloc[0]["Nombre"].lower()
    else:
        explicativo = None
    
    result = {"mejor": ganador}
    if creativo:
        result["creativo"] = creativo
    if explicativo:
        result["explicativo"] = explicativo
    
    return result


# === Función para descargar notebook oficial ===
def descargar_notebook_oficial(url):
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
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
                contenido = response.read()
                contenido_str = contenido.decode("utf-8")
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
    st.session_state.evaluacion = None

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

    # === Fase 1: Evaluar originalidad ===
    with st.spinner("🔍 Fase 1/2: Evaluando originalidad..."):
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
                except:
                    st.error("❌ Error al leer el notebook.")
                    st.stop()

        notebook_oficial = descargar_notebook_oficial(SOLUCION_OFICIAL_URL)
        
        if not notebook_oficial:
            st.error("❌ No se pudo descargar el notebook oficial.")
            st.stop()

        originalidad, similitud = evaluar_originalidad(notebook_usuario, notebook_oficial)
        st.session_state.similitud = similitud

    # === Mostrar resultado de originalidad ===
    if originalidad == "Copia directa":
        st.error(f"🚫 **COPIA DIRECTA DETECTADA** (Similitud: {similitud*100:.1f}%)")
        st.warning("Tu notebook es idéntico al oficial. No se evaluará.")
        evaluacion_ia = {
            "nota_total": 0.0,
            "exploracion": 0,
            "preprocesamiento": 0,
            "modelos": 0,
            "evaluacion": 0,
            "documentacion": 0,
            "comentario": "Copia directa detectada.",
            "puntos_fuertes": [],
            "areas_mejora": ["Hacer trabajo original"]
        }
    else:
        if originalidad == "Copia modificada":
            st.warning(f"⚠️ **Copia con modificaciones** (Similitud: {similitud*100:.1f}%)")
        elif originalidad == "Inspirado":
            st.info(f"💡 **Trabajo inspirado** (Similitud: {similitud*100:.1f}%)")
        else:
            st.success(f"🎉 **Trabajo original** (Similitud: {similitud*100:.1f}%)")
        
        # === Fase 2: Evaluar con IA ===
        with st.spinner("🤖 Fase 2/2: Evaluando con IA (esto puede tardar unos segundos)..."):
            evaluacion_ia = evaluar_respuestas_ia(notebook_usuario)
    
    st.session_state.evaluacion = evaluacion_ia
    
    # === Mostrar resultados ===
    if evaluacion_ia["nota_total"] > 0:
        st.markdown("---")
        st.subheader("📊 Evaluación Automática con IA")
        
        # Nota principal
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            nota_color = "🟢" if evaluacion_ia["nota_total"] >= 7 else "🟡" if evaluacion_ia["nota_total"] >= 5 else "🔴"
            st.metric("Nota Final", f"{nota_color} {evaluacion_ia['nota_total']}/10")
        with col2:
            st.metric("Exploración", f"{evaluacion_ia['exploracion']}/2")
        with col3:
            st.metric("Preproc.", f"{evaluacion_ia['preprocesamiento']}/2")
        with col4:
            st.metric("Modelos", f"{evaluacion_ia['modelos']}/3")
        with col5:
            st.metric("Evaluación", f"{evaluacion_ia['evaluacion']}/2")
        
        # Comentario
        st.info(f"**📝 Evaluación del profesor IA:** {evaluacion_ia['comentario']}")
        
        # Puntos fuertes
        if evaluacion_ia.get("puntos_fuertes") and len(evaluacion_ia["puntos_fuertes"]) > 0:
            st.success("**✅ Puntos fuertes:**")
            for punto in evaluacion_ia["puntos_fuertes"]:
                st.write(f"• {punto}")
        
        # Áreas de mejora
        if evaluacion_ia.get("areas_mejora") and len(evaluacion_ia["areas_mejora"]) > 0:
            st.warning("**💡 Áreas de mejora:**")
            for area in evaluacion_ia["areas_mejora"]:
                st.write(f"• {area}")
        
        # Calificación final
        if evaluacion_ia["nota_total"] >= 7:
            st.success("✅ ¡Excelente trabajo!")
            if originalidad in ["Original", "Inspirado"]:
                st.balloons()
        elif evaluacion_ia["nota_total"] >= 5:
            st.info("ℹ️ Buen trabajo, pero hay margen de mejora.")
        else:
            st.warning("⚠️ El trabajo necesita mejoras significativas.")

    # === Guardar evaluación ===
    guardar_evaluacion(nombre, CAPITULO, fecha, originalidad, similitud, evaluacion_ia)

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

# === Leyenda ===
with st.expander("📘 ¿Qué significan los emojis?"):
    st.markdown("""
    - 🏆 **Mejor entrega**: Mayor puntuación combinada (originalidad + nota IA).  
    - 🎨 **Mención creativa**: La entrega más original.  
    - 📝 **Mención explicativa**: Mejor documentación.  
    - ✅ **Entrega válida**: Subida correcta.  
    - ❌ **No entregado**: Sin práctica subida.
    """)

# === Mensaje de éxito ===
if st.session_state.archivo_guardado:
    st.markdown("---")
    st.markdown(f"""
    ### 🎉 Entrega completada
    
    - **Archivo:** `{st.session_state.archivo_nombre}`  
    - **Autor:** `{st.session_state.archivo_autor}`  
    - **Similitud:** `{st.session_state.similitud*100:.1f}%`
    - **Estado:** ✅ Registro actualizado
    
    🙌 ¡Gracias por tu participación en nuestra ~~secta~~ comunidad!
    """)

    if st.button("¿Quieres subir otro archivo?"):
        for key in ["archivo_guardado", "archivo_nombre", "archivo_autor", "similitud", "evaluacion"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
import streamlit as st
import os
import re
import pandas as pd
import zipfile
import json
from datetime import datetime
from difflib import SequenceMatcher
import urllib.request
import ssl
import requests
import base64
from io import BytesIO
from pathlib import Path


#  Configuración del capítulo 
CAPITULO = "Capítulo 2"
COLUMNA = "Capítulo 2"
CARPETA_DESTINO = "capitulo_02"
FECHA_LIMITE = datetime(2025, 11, 9)

# Configuración de GitHub
GITHUB_OWNER = "eortas"  # Tu usuario de GitHub
GITHUB_REPO = "Machine_learning_secta"  # Nombre del repositorio
GITHUB_BRANCH = "main"  # Rama principal

TOKEN = st.secrets["GITHUB_TOKEN"]

#  Funciones para GitHub API 

def obtener_archivo_github(ruta_archivo):
    """
    Descarga un archivo del repositorio de GitHub
    """
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{ruta_archivo}"
    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        response = requests.get(url, headers=headers, params={"ref": GITHUB_BRANCH})
        if response.status_code == 200:
            content = response.json()
            # Decodificar contenido base64
            file_content = base64.b64decode(content["content"]).decode("utf-8")
            return file_content, content["sha"]
        elif response.status_code == 404:
            return None, None
        else:
            st.error(f"Error al obtener archivo: {response.status_code}")
            return None, None
    except Exception as e:
        st.error(f"Error: {e}")
        return None, None


def obtener_sha_github(ruta_archivo):
    """
    Comprueba si un archivo existe en GitHub y devuelve su SHA si existe.
    """
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{ruta_archivo}"
    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        response = requests.get(url, headers=headers, params={"ref": GITHUB_BRANCH})
        if response.status_code == 200:
            return response.json().get("sha")
        elif response.status_code == 404:
            return None
        else:
            st.error(f"Error al obtener SHA: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error al obtener SHA: {e}")
        return None


def subir_archivo_github(ruta_archivo, contenido, mensaje_commit, sha=None):
    """
    Sube o actualiza un archivo en GitHub.

    Si el archivo ya existe, lo actualiza (usa el SHA actual).
    Si no existe, lo crea desde cero.
    """
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{ruta_archivo}"
    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Convertir contenido a base64
    if isinstance(contenido, str):
        contenido_base64 = base64.b64encode(contenido.encode()).decode()
    else:
        contenido_base64 = base64.b64encode(contenido).decode()

    # 1️⃣ Obtener SHA actual (si el archivo existe)
    sha = obtener_sha_github(ruta_archivo)

    # 2️⃣ Crear el payload de subida
    data = {
        "message": mensaje_commit,
        "content": contenido_base64,
        "branch": GITHUB_BRANCH
    }
    if sha:
        data["sha"] = sha  # necesario si se actualiza el archivo

    # 3️⃣ Subir o actualizar
    try:
        response = requests.put(url, headers=headers, json=data)
        if response.status_code in (200, 201):
            return True
        else:
            st.error(f"Error al subir archivo: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        st.error(f"Error al subir archivo: {e}")
        return False


def obtener_csv_como_dataframe(ruta_csv):
    """
    Obtiene un CSV de GitHub y lo convierte en DataFrame
    """
    contenido, sha = obtener_archivo_github(ruta_csv)
    if contenido:
        from io import StringIO
        df = pd.read_csv(StringIO(contenido))
        return df, sha
    return None, None


def guardar_dataframe_en_github(df, ruta_csv, mensaje_commit, sha=None):
    """
    Guarda un DataFrame como CSV en GitHub
    """
    csv_string = df.to_csv(index=False)
    return subir_archivo_github(ruta_csv, csv_string, mensaje_commit, sha)

# URL del notebook oficial
SOLUCION_OFICIAL_URL = "https://github.com/ageron/handson-ml3/raw/main/02_end_to_end_machine_learning_project.ipynb"

# API Key para Groq (añadir a secrets.toml)
# Gratis en https://console.groq.com/
try:
    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
except:
    GROQ_API_KEY = ""


#  Enunciado del ejercicio 
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


# Función para extraer contenido del notebook (código y markdown)
def extraer_contenido_notebook(notebook):
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


# Evaluación con Groq
def evaluar_con_groq(notebook_usuario):
    if not GROQ_API_KEY:
        return None
    
    contenido = extraer_contenido_notebook(notebook_usuario)
    
    # Limita el contenido para no exceder tokens (groq tiene limite de 6000 tokens por minuto)
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

Devuelve tu respuesta en este formato JSON exacto (usa números decimales con 1 decimal, por ejemplo 7.5):
{{
    "nota_total": 7.5,
    "exploracion": 1.8,
    "preprocesamiento": 1.5,
    "modelos": 2.2,
    "evaluacion": 1.5,
    "documentacion": 0.5,
    "comentario": "El estudiante demuestra buena comprensión...",
    "puntos_fuertes": ["Buen análisis exploratorio", "Implementación correcta de modelos"],
    "areas_mejora": ["Falta profundidad en evaluación", "Mejorar documentación"]
}}

IMPORTANTE: Todos los números deben tener formato decimal (ejemplo: 7.5, no 7). La suma de las partes debe coincidir con la nota_total.
Sé justo pero exigente sin paternalismo pero tampoco desmotivador. Solo da puntuación completa si el trabajo es excelente."""

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
                        "model": "llama-3.3-70b-versatile",  # se puede cambiar a otros modelos disponibles en groq
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
                    
                    # Extrae JSON de la respuesta
                    inicio = contenido_respuesta.find('{')
                    fin = contenido_respuesta.rfind('}') + 1
                    
                    if inicio != -1 and fin > inicio:
                        json_str = contenido_respuesta[inicio:fin]
                        evaluacion = json.loads(json_str)
                        return evaluacion
                
                # Si hay rate limit, esperar y reintentar
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


#  Evaluación principal 
def evaluar_respuestas_ia(notebook_usuario):
    """
    Evalúa el notebook usando IA con Groq
    """
    evaluacion = evaluar_con_groq(notebook_usuario)
    
    if evaluacion:
        return evaluacion
    
    # Si falla, retornar evaluación por defecto
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


#  Evaluación de originalidad 
def evaluar_originalidad(contenido_usuario, contenido_oficial):
    """
    Compara el código ejecutable de ambos notebooks (más robusto contra traducciones)
    """
    # Método 1: Similitud de JSON completo (detecta copias exactas)
    str_usuario = json.dumps(contenido_usuario, sort_keys=True)
    str_oficial = json.dumps(contenido_oficial, sort_keys=True)
    sim_json = SequenceMatcher(None, str_usuario, str_oficial).ratio()
    
    # Método 2: Similitud de código ejecutable (detecta copias traducidas)
    def extraer_codigo_ejecutable(notebook):
        """Extrae solo las líneas de código ejecutable, sin comentarios ni markdown"""
        lineas_codigo = []
        for cell in notebook.get('cells', []):
            if cell.get('cell_type') == 'code':
                source = ''.join(cell.get('source', []))
                for linea in source.split('\n'):
                    linea_limpia = linea.strip()
                    # Solo código ejecutable (sin comentarios ni líneas vacías)
                    if linea_limpia and not linea_limpia.startswith('#'):
                        lineas_codigo.append(linea_limpia)
        return '\n'.join(lineas_codigo)
    
    codigo_usuario = extraer_codigo_ejecutable(contenido_usuario)
    codigo_oficial = extraer_codigo_ejecutable(contenido_oficial)
    sim_codigo = SequenceMatcher(None, codigo_usuario, codigo_oficial).ratio()
    
    # Usar la similitud más alta (la que mejor detecte la copia)
    similitud_maxima = max(sim_json, sim_codigo)
    
    # Determinar originalidad
    if similitud_maxima > 0.95 or sim_codigo > 0.95:
        originalidad = "Copia directa"
    elif similitud_maxima > 0.85 or sim_codigo > 0.90:
        originalidad = "Copia modificada"
    elif similitud_maxima > 0.7:
        originalidad = "Inspirado"
    else:
        originalidad = "Original"
    
    return originalidad, similitud_maxima


#  Guardar evaluación completa 
def guardar_evaluacion(nombre, capitulo, fecha, originalidad, similitud, evaluacion_ia):
    """
    Guarda toda la información de la evaluación en GitHub
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
    
    ruta_csv = "evaluaciones/evaluacion_originalidad.csv"
    
    # Obtener CSV existente de GitHub
    df_eval, sha = obtener_csv_como_dataframe(ruta_csv)
    
    if df_eval is not None:
        # Añadir nueva fila
        df_eval = pd.concat([df_eval, pd.DataFrame([fila])], ignore_index=True)
    else:
        # Crear nuevo DataFrame
        df_eval = pd.DataFrame([fila])
        sha = None
    
    # Guardar en GitHub
    mensaje = f"Evaluación de {nombre} - {capitulo} - Nota: {evaluacion_ia['nota_total']}/10"
    return guardar_dataframe_en_github(df_eval, ruta_csv, mensaje, sha)


#  Hall of Fame 
def generar_hall_of_fame(capitulo):
    ruta_csv = "evaluaciones/evaluacion_originalidad.csv"
    df_eval, _ = obtener_csv_como_dataframe(ruta_csv)
    
    if df_eval is None:
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


#  Función para descargar notebook oficial 
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


#  Configuración visual 
st.set_page_config(layout="centered", page_title="Entregas ML secta post bootcamp")

def set_background(image_path: str):
    """
    Inserta un fondo de pantalla en la app de Streamlit.
    Acepta rutas locales (relativas o absolutas) o URLs.
    """
    if Path(image_path).exists():
        with open(image_path, "rb") as f:
            data_uri = f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
        background = f"url('{data_uri}')"
    else:
        # Si es una URL, la usa directamente
        background = f"url('{image_path}')"

    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: {background};
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        [data-testid="stHeader"], [data-testid="stToolbar"] {{
            background: rgba(0, 0, 0, 0);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# === APLICA EL WALLPAPER AQUÍ ===
set_background("https://i.ibb.co/5hQgj6hr/fondo-ml.jpg") 

#  Fecha límite 
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

#  Carga del registro desde GitHub 
REGISTRO_PATH_GITHUB = "uploads/registro_entregas.csv"
df, df_sha = obtener_csv_como_dataframe(REGISTRO_PATH_GITHUB)

if df is None:
    st.error("No se encuentra el archivo registro_entregas.csv en el repositorio.")
    st.stop()

if COLUMNA not in df.columns:
    df[COLUMNA] = ""

#  Estado de subida 
if "archivo_guardado" not in st.session_state:
    st.session_state.archivo_guardado = False
    st.session_state.archivo_nombre = ""
    st.session_state.archivo_autor = ""
    st.session_state.similitud = 0
    st.session_state.evaluacion = None

#  Subida de archivo 
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

    fecha = hoy.strftime("%Y-%m-%d")
    
    # Leer archivo ZIP desde memoria (sin guardarlo localmente)
    archivo_bytes = archivo.read()

    #  Fase 1: Evaluar originalidad 
    with st.spinner("🔍 Fase 1/2: Evaluando originalidad..."):
        notebook_usuario = None
        nombre_notebook = None
        
        # Leer ZIP desde memoria
        with zipfile.ZipFile(BytesIO(archivo_bytes), 'r') as zip_ref:
            archivos_ipynb = [f for f in zip_ref.namelist() if f.endswith(".ipynb") and not f.startswith("__MACOSX")]
            
            if not archivos_ipynb:
                st.error("❌ El archivo .zip no contiene ningún notebook (.ipynb).")
                st.stop()
            
            notebook_file = archivos_ipynb[0]
            nombre_notebook = os.path.basename(notebook_file)
            
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

    #  Mostrar resultado de originalidad 
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
        
        #  Fase 2: Evaluar con IA 
        with st.spinner("🤖 Fase 2/2: Evaluando con IA (esto puede tardar unos segundos)..."):
            evaluacion_ia = evaluar_respuestas_ia(notebook_usuario)
    
    st.session_state.evaluacion = evaluacion_ia
    
    #  Mostrar resultados 
    if evaluacion_ia["nota_total"] > 0:
        st.markdown("---")
        st.subheader("📊 Evaluación Automática con IA")
        
        # Nota principal (grande y destacada)
        nota_total = evaluacion_ia['nota_total']
        nota_color = "🟢" if nota_total >= 7 else "🟡" if nota_total >= 5 else "🔴"
        
        st.markdown(f"""
        <div style='text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px; margin-bottom: 20px;'>
            <h1 style='margin: 0; color: #262730;'>{nota_color} {nota_total:.1f}/10</h1>
            <p style='margin: 5px 0 0 0; color: #666;'>Nota Final</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Desglose por categorías
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Exploración", f"{evaluacion_ia['exploracion']:.1f}/2")
        with col2:
            st.metric("Preprocesamiento", f"{evaluacion_ia['preprocesamiento']:.1f}/2")
        with col3:
            st.metric("Modelos", f"{evaluacion_ia['modelos']:.1f}/3")
        with col4:
            st.metric("Evaluación", f"{evaluacion_ia['evaluacion']:.1f}/2")
        with col5:
            st.metric("Documentación", f"{evaluacion_ia['documentacion']:.1f}/1")
        
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

    #  Subir archivos a GitHub 
    with st.spinner("📤 Subiendo archivos a GitHub..."):
        # 1. Guardar evaluación en CSV
        exito_eval = guardar_evaluacion(nombre, CAPITULO, fecha, originalidad, similitud, evaluacion_ia)
        
        # 2. Subir archivo ZIP
        ruta_zip = f"uploads/{CARPETA_DESTINO}/{archivo.name}"
        mensaje_zip = f"{CAPITULO} - ZIP de {nombre} ({fecha})"
        exito_zip = subir_archivo_github(ruta_zip, archivo_bytes, mensaje_zip)
        
        # 3. Subir notebook extraído
        notebook_json = json.dumps(notebook_usuario, ensure_ascii=False, indent=2)
        ruta_notebook = f"soluciones_alumnos/{CARPETA_DESTINO}/{nombre}_{fecha}.ipynb"
        mensaje_notebook = f"{CAPITULO} - Notebook de {nombre} ({fecha})"
        exito_notebook = subir_archivo_github(ruta_notebook, notebook_json, mensaje_notebook)
        
        # 4. Actualizar registro de entregas
        df.loc[df["Nombre"].str.lower() == nombre, COLUMNA] = "✅"
        mensaje_registro = f"{CAPITULO} - Registro actualizado para {nombre} ({fecha})"
        exito_registro = guardar_dataframe_en_github(df, REGISTRO_PATH_GITHUB, mensaje_registro, df_sha)
        
        # Verificar que todo se subió correctamente
        if exito_eval and exito_zip and exito_notebook and exito_registro:
            st.success("✅ Analisis completo, si quieres puedes subir otro archivo más adelante 😊.")
        else:
            st.warning("⚠️ Algunos archivos no se pudieron subir:")
            if not exito_eval:
                st.error("- Evaluación")
            if not exito_zip:
                st.error("- Archivo ZIP")
            if not exito_notebook:
                st.error("- Notebook extraído")
            if not exito_registro:
                st.error("- Registro de entregas")

    st.session_state.archivo_guardado = True
    st.session_state.archivo_nombre = archivo.name
    st.session_state.archivo_autor = nombre

#  Hall of Fame 
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

#  Tabla de entregas 
st.subheader("Listado de miembros y estado de entregas")
st.dataframe(df_show, use_container_width=True)

#  Leyenda 
with st.expander("📘 ¿Qué significan los emojis?"):
    st.markdown("""
    - 🏆 **Mejor entrega**: Mayor puntuación combinada (originalidad + nota IA).  
    - 🎨 **Mención creativa**: La entrega más original.  
    - 📝 **Mención explicativa**: Mejor documentación.  
    - ✅ **Entrega válida**: Subida correcta.  
    - ❌ **No entregado**: Sin práctica subida.
    """)

#  Mensaje de éxito 
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

    

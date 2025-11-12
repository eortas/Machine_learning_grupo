"""
Sistema de entregas - Versión ultra simplificada
"""
import streamlit as st
import os
from datetime import datetime
import pytz

# Importa módulos personalizados
from config.settings import (
    CAPITULO, COLUMNA, CARPETA_DESTINO, FECHA_LIMITE,
    REPO_URL, REPO_DIR, TOKEN, REGISTRO_PATH,
    SOLUCION_OFICIAL_URL
)
from core.git_manager import inicializar_repo, commit_y_push
from data.data_manager import (
    cargar_registro, actualizar_registro,
    guardar_evaluacion, generar_hall_of_fame
)
from core.validators import validar_nombre_archivo, validar_nombre_en_lista
from core.file_processor import guardar_archivo_zip, procesar_archivo_zip
from utils.notebook_utils import descargar_notebook_oficial
from evaluacion.evaluacion_originalidad import evaluar_originalidad
from evaluacion.evaluacion_ia import evaluar_respuestas_ia
from evaluacion.cierre_capitulo_simple import verificar_cierre_automatico
from ui.ui_components import (
    mostrar_header, mostrar_resultado_originalidad,
    mostrar_evaluacion_ia, mostrar_tabla_entregas,
    mostrar_mensaje_exito
)

st.set_page_config(layout="centered", page_title="Entregas ML grupo lectura post bootcamp")

def inicializar_session_state():
    if "archivo_guardado" not in st.session_state:
        st.session_state.archivo_guardado = False
        st.session_state.archivo_nombre = ""
        st.session_state.archivo_autor = ""
        st.session_state.similitud = 0
        st.session_state.evaluacion = None

def main():
    mostrar_header(CAPITULO, FECHA_LIMITE)
    
    try:
        repo = inicializar_repo(REPO_DIR, REPO_URL, TOKEN)
    except Exception as e:
        st.error(f"❌ Error Git: {str(e)}")
        st.stop()
    
    df = cargar_registro(REPO_DIR, REGISTRO_PATH)
    if df is None:
        st.error("No se encuentra registro_entregas.csv")
        st.stop()
    
    if COLUMNA not in df.columns:
        df[COLUMNA] = ""
    
    inicializar_session_state()
    
    # VERIFICACIÓN DIRECTA SIN FUNCIONES
    madrid_tz = pytz.timezone('Europe/Madrid')
    ahora = datetime.now(madrid_tz)
    
    fecha_limite_check = FECHA_LIMITE
    if fecha_limite_check.tzinfo is None:
        fecha_limite_check = madrid_tz.localize(fecha_limite_check)
    else:
        fecha_limite_check = fecha_limite_check.astimezone(madrid_tz)
    
    plazo_vencido = ahora > fecha_limite_check
    
    # Si está vencido, mostrar tabla de Hall of Fame
    if plazo_vencido:
        st.write("---")
        st.subheader("🎖️ ENTREGAS - CAPÍTULO CERRADO")
        
        # Intentar cerrar
        verificar_cierre_automatico(CAPITULO, COLUMNA, REPO_DIR, REGISTRO_PATH, FECHA_LIMITE)
        
        # Recargar df
        df = cargar_registro(REPO_DIR, REGISTRO_PATH)
        
        # Mostrar tabla
        hall = generar_hall_of_fame(COLUMNA, REPO_DIR)
        mostrar_tabla_entregas(df, COLUMNA, hall)
        
        st.error("❌ El plazo de entrega ha finalizado.")
        return  # IMPORTANTE: Sale aquí, no muestra uploader
    
    # SI NO ESTÁ VENCIDO, mostrar uploader
    archivo = st.file_uploader(
        "Sube tu archivo .zip (capX-nombre.zip)",
        type=["zip"],
        key="uploader"
    )
    
    if archivo and not st.session_state.archivo_guardado:
        procesar_entrega(archivo, df, repo)
    
    hall = generar_hall_of_fame(COLUMNA, REPO_DIR)
    mostrar_tabla_entregas(df, COLUMNA, hall)
    
    if st.session_state.archivo_guardado:
        mostrar_mensaje_exito(
            st.session_state.archivo_nombre,
            st.session_state.archivo_autor,
            st.session_state.similitud
        )

def procesar_entrega(archivo, df, repo):
    es_valido, capitulo_archivo, nombre = validar_nombre_archivo(archivo.name)
    
    if not es_valido:
        st.error("❌ Formato inválido: usa capX-nombre.zip")
        st.stop()
    
    if not validar_nombre_en_lista(nombre, df["Nombre"].values):
        st.error(f"El nombre '{nombre}' no está en la lista.")
        st.stop()
    
    carpeta_capitulo = os.path.join(REPO_DIR, "uploads", CARPETA_DESTINO)
    carpeta_soluciones = os.path.join(REPO_DIR, "soluciones_alumnos", CARPETA_DESTINO)
    fecha = datetime.now().strftime("%Y-%m-%d")
    
    filepath = guardar_archivo_zip(archivo, carpeta_capitulo)
    
    with st.spinner("🔍 Evaluando originalidad..."):
        notebook_usuario, nombre_notebook = procesar_archivo_zip(
            filepath, carpeta_soluciones, nombre, fecha
        )
        
        if notebook_usuario is None:
            st.error("❌ No hay notebook .ipynb en el .zip")
            st.stop()
        
        notebook_oficial = descargar_notebook_oficial(SOLUCION_OFICIAL_URL)
        if not notebook_oficial:
            st.error("❌ No se pudo descargar el notebook oficial.")
            st.stop()
        
        originalidad, similitud = evaluar_originalidad(notebook_usuario, notebook_oficial)
        st.session_state.similitud = similitud
    
    mostrar_resultado_originalidad(originalidad, similitud)
    
    if originalidad == "Copia directa":
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
        with st.spinner("🤖 Evaluando con IA..."):
            evaluacion_ia = evaluar_respuestas_ia(notebook_usuario)
    
    st.session_state.evaluacion = evaluacion_ia
    mostrar_evaluacion_ia(evaluacion_ia, originalidad)
    
    guardar_evaluacion(nombre, CAPITULO, fecha, originalidad, similitud, evaluacion_ia, REPO_DIR)
    actualizar_registro(df, nombre, COLUMNA, REPO_DIR, REGISTRO_PATH)
    
    mensaje_commit = f"{CAPITULO} - {nombre} - Nota: {evaluacion_ia['nota_total']}/10"
    commit_y_push(repo, mensaje_commit)
    
    st.session_state.archivo_guardado = True
    st.session_state.archivo_nombre = archivo.name
    st.session_state.archivo_autor = nombre

if __name__ == "__main__":
    main()
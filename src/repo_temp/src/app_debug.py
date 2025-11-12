"""
Sistema de entregas de prácticas de Machine Learning
Aplicación principal con Streamlit - Versión con DEBUG
"""
import streamlit as st
import os
from datetime import datetime

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


# Configuración visual de Streamlit
st.set_page_config(layout="centered", page_title="Entregas ML grupo lectura post bootcamp")


def inicializar_session_state():
    """Inicializa el estado de la sesión de Streamlit."""
    if "archivo_guardado" not in st.session_state:
        st.session_state.archivo_guardado = False
        st.session_state.archivo_nombre = ""
        st.session_state.archivo_autor = ""
        st.session_state.similitud = 0
        st.session_state.evaluacion = None


def main():
    """Función principal de la aplicación."""
    # Muestra header con fecha límite
    mostrar_header(CAPITULO, FECHA_LIMITE)
    
    # Inicializar repositorio Git
    repo = inicializar_repo(REPO_DIR, REPO_URL, TOKEN)
    
    # Carga registro de entregas
    df = cargar_registro(REPO_DIR, REGISTRO_PATH)
    if df is None:
        st.error("No se encuentra el archivo registro_entregas.csv en el repositorio.")
        st.stop()
    
    if COLUMNA not in df.columns:
        df[COLUMNA] = ""
    
    # Verifica cierre automático al terminar el plazo
    if verificar_cierre_automatico(CAPITULO, COLUMNA, REPO_DIR, REGISTRO_PATH, FECHA_LIMITE):
        # Recargar registro con emojis actualizados
        df = cargar_registro(REPO_DIR, REGISTRO_PATH)
        
        # Commit automático
        repo.git.add(".")
        repo.index.commit(f"Cierre de {CAPITULO} - Hall of Fame")
        repo.remote(name="origin").push()
        
        st.success("🏆 Hall of Fame generado. Emojis especiales asignados a los ganadores.")
        st.info("🔄 Recarga la página para ver los cambios")
    
    # Inicializa estado de la sesión
    inicializar_session_state()
    
    # Subida de archivo
    archivo = st.file_uploader(
        "Sube tu archivo .zip. Recuerda usar el formato capX-nombre.zip (ej. cap2-pepe.zip)",
        type=["zip"],
        key="uploader"
    )
    
    if archivo and not st.session_state.archivo_guardado:
        procesar_entrega(archivo, df, repo)
    
    # Hall of Fame y tabla de entregas
    hall = generar_hall_of_fame(COLUMNA, REPO_DIR)
    mostrar_tabla_entregas(df, COLUMNA, hall)
    
    # Mensaje de éxito si la entrega se completó
    if st.session_state.archivo_guardado:
        mostrar_mensaje_exito(
            st.session_state.archivo_nombre,
            st.session_state.archivo_autor,
            st.session_state.similitud
        )


def procesar_entrega(archivo, df, repo):
    """
    Procesa la entrega de un archivo.
    
    Args:
        archivo: Archivo subido por el usuario
        df: DataFrame con el registro de entregas
        repo: Objeto del repositorio Git
    """
    # Validar nombre del archivo
    es_valido, capitulo_archivo, nombre = validar_nombre_archivo(archivo.name)
    
    if not es_valido:
        st.error("❌ Nombre de archivo no válido. Usa el formato: capX-nombre.zip (ej. cap2-pepe.zip)")
        st.stop()
    
    # Validar que el nombre esté en la lista
    if not validar_nombre_en_lista(nombre, df["Nombre"].values):
        st.error(f"El nombre '{nombre}' no está en la lista de miembros válidos.")
        st.stop()
    
    # Prepara las carpetas
    carpeta_capitulo = os.path.join(REPO_DIR, "uploads", CARPETA_DESTINO)
    carpeta_soluciones = os.path.join(REPO_DIR, "soluciones_alumnos", CARPETA_DESTINO)
    
    fecha = datetime.now().strftime("%Y-%m-%d")
    
    # Guarda archivo ZIP
    filepath = guardar_archivo_zip(archivo, carpeta_capitulo)
    
    # Fase 1: Evaluar originalidad
    with st.spinner("🔍 Fase 1/2: Evaluando originalidad..."):
        # Procesar archivo ZIP y extraer notebook
        notebook_usuario, nombre_notebook = procesar_archivo_zip(
            filepath, carpeta_soluciones, nombre, fecha
        )
        
        if notebook_usuario is None:
            st.error("❌ El archivo .zip no contiene ningún notebook (.ipynb) válido.")
            st.stop()
        
        # Descarga notebook oficial
        notebook_oficial = descargar_notebook_oficial(SOLUCION_OFICIAL_URL)
        
        if not notebook_oficial:
            st.error("❌ No se pudo descargar el notebook oficial.")
            st.stop()
        
        # Evalua originalidad
        originalidad, similitud = evaluar_originalidad(notebook_usuario, notebook_oficial)
        st.session_state.similitud = similitud
    
    # Muestra resultado de originalidad
    mostrar_resultado_originalidad(originalidad, similitud)
    
    # Fase 2: Evalua con Groq
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
        with st.spinner("🤖 Fase 2/2: Evaluando con IA (esto puede tardar unos segundos)..."):
            evaluacion_ia = evaluar_respuestas_ia(notebook_usuario)
    
    st.session_state.evaluacion = evaluacion_ia
    
    # DEBUG: Ver qué recibe app.py de evaluar_respuestas_ia
    suma_debug = (
        evaluacion_ia.get('exploracion', 0) +
        evaluacion_ia.get('preprocesamiento', 0) +
        evaluacion_ia.get('modelos', 0) +
        evaluacion_ia.get('evaluacion', 0) +
        evaluacion_ia.get('documentacion', 0)
    )
    st.error(f"""
    🔍 DEBUG APP.PY (justo después de evaluar_respuestas_ia):
    - nota_total: {evaluacion_ia['nota_total']}
    - suma componentes: {suma_debug}
    - TIPO nota_total: {type(evaluacion_ia['nota_total'])}
    """)
    
    # Muestra evaluación
    mostrar_evaluacion_ia(evaluacion_ia, originalidad)
    
    # DEBUG: Ver qué se pasa a guardar_evaluacion
    st.error(f"🔍 DEBUG APP.PY (antes de guardar_evaluacion): nota_total={evaluacion_ia['nota_total']}")
    
    # Guarda evaluación
    guardar_evaluacion(nombre, CAPITULO, fecha, originalidad, similitud, evaluacion_ia, REPO_DIR)
    
    # DEBUG: Ver qué hay después de guardar_evaluacion
    st.error(f"🔍 DEBUG APP.PY (después de guardar_evaluacion): nota_total={evaluacion_ia['nota_total']}")
    
    # Actualiza registro
    actualizar_registro(df, nombre, COLUMNA, REPO_DIR, REGISTRO_PATH)
    
    # Commit y push
    mensaje_commit = f"{CAPITULO} - Subida de {nombre} ({fecha}) - Nota: {evaluacion_ia['nota_total']}/10"
    commit_y_push(repo, mensaje_commit)
    
    # Marca como guardado
    st.session_state.archivo_guardado = True
    st.session_state.archivo_nombre = archivo.name
    st.session_state.archivo_autor = nombre


if __name__ == "__main__":
    main()
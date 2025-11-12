"""
Funciones para procesar archivos ZIP con notebooks
"""
import os
import json
import zipfile
from datetime import datetime


def procesar_archivo_zip(filepath, carpeta_soluciones, nombre, fecha):
    """
    Procesa un archivo ZIP extrayendo el notebook y guardándolo.
    
    Args:
        filepath: Ruta al archivo ZIP
        carpeta_soluciones: Carpeta donde guardar el notebook extraído
        nombre: Nombre del estudiante
        fecha: Fecha de entrega
        
    Returns:
        tuple: (notebook_usuario, nombre_notebook) o (None, None) si hay error
    """
    notebook_usuario = None
    nombre_notebook = None
    
    try:
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            archivos_ipynb = [
                f for f in zip_ref.namelist() 
                if f.endswith(".ipynb") and not f.startswith("__MACOSX")
            ]
            
            if not archivos_ipynb:
                return None, None
            
            notebook_file = archivos_ipynb[0]
            nombre_notebook = os.path.basename(notebook_file)
            
            with zip_ref.open(notebook_file) as f:
                notebook_usuario = json.load(f)
        
        # Guarda el notebook extraído en la carpeta de soluciones
        nombre_archivo_solucion = f"{nombre}_{fecha}.ipynb"
        ruta_solucion = os.path.join(carpeta_soluciones, nombre_archivo_solucion)
        
        os.makedirs(carpeta_soluciones, exist_ok=True)
        
        with open(ruta_solucion, 'w', encoding='utf-8') as f:
            json.dump(notebook_usuario, f, ensure_ascii=False, indent=2)
        
        return notebook_usuario, nombre_notebook
        
    except Exception as e:
        return None, None


def guardar_archivo_zip(archivo, carpeta_destino):
    """
    Guarda el archivo ZIP subido en la carpeta de destino.
    
    Args:
        archivo: Objeto del archivo subido (UploadedFile de Streamlit)
        carpeta_destino: Carpeta donde guardar el archivo
        
    Returns:
        str: Ruta completa del archivo guardado
    """
    os.makedirs(carpeta_destino, exist_ok=True)
    filepath = os.path.join(carpeta_destino, archivo.name)
    
    with open(filepath, "wb") as f:
        f.write(archivo.getbuffer())
    
    return filepath

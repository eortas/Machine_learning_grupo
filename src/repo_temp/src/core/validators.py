"""
Funciones para validar archivos y nombres
"""
import re


def validar_nombre_archivo(nombre_archivo):
    """
    Valida que el nombre del archivo siga el formato correcto: capX-nombre.zip
    
    Args:
        nombre_archivo: Nombre del archivo a validar
        
    Returns:
        tuple: (es_valido, capitulo, nombre) o (False, None, None) si no es válido
    """
    patron = r"^(cap\d{1,2})-([a-zA-Z0-9_]+)\.zip$"
    match = re.match(patron, nombre_archivo)
    
    if not match:
        return False, None, None
    
    capitulo_archivo, nombre = match.groups()
    nombre = nombre.lower()
    
    return True, capitulo_archivo, nombre


def validar_nombre_en_lista(nombre, lista_nombres):
    """
    Valida que el nombre esté en la lista de nombres válidos.
    
    Args:
        nombre: Nombre a validar
        lista_nombres: Lista de nombres válidos
        
    Returns:
        bool: True si el nombre es válido, False en caso contrario
    """
    nombres_validos = [n.lower() for n in lista_nombres]
    return nombre.lower() in nombres_validos

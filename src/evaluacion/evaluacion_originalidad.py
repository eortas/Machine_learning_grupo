"""
Funciones para evaluar la originalidad de los notebooks
"""
import json
from difflib import SequenceMatcher
from utils.notebook_utils import extraer_codigo_ejecutable


def evaluar_originalidad(contenido_usuario, contenido_oficial):
    """
    Evalúa la originalidad de un notebook comparándolo con la solución oficial.
    
    Args:
        contenido_usuario: Notebook del estudiante en formato JSON
        contenido_oficial: Notebook oficial en formato JSON
        
    Returns:
        tuple: (originalidad, similitud_maxima)
            - originalidad: str ("Copia directa", "Copia modificada", "Inspirado", "Original")
            - similitud_maxima: float (0.0 a 1.0)
    """
    # Método 1: Similitud de JSON completo (detecta copias exactas)
    str_usuario = json.dumps(contenido_usuario, sort_keys=True)
    str_oficial = json.dumps(contenido_oficial, sort_keys=True)
    sim_json = SequenceMatcher(None, str_usuario, str_oficial).ratio()
    
    # Método 2: Similitud de código ejecutable
    codigo_usuario = extraer_codigo_ejecutable(contenido_usuario)
    codigo_oficial = extraer_codigo_ejecutable(contenido_oficial)
    sim_codigo = SequenceMatcher(None, codigo_usuario, codigo_oficial).ratio()
    
    # Usa la similitud más alta (la que mejor detecte la copia)
    similitud_maxima = max(sim_json, sim_codigo)
    
    # Determina originalidad
    if similitud_maxima > 0.95 or sim_codigo > 0.95:
        originalidad = "Copia directa"
    elif similitud_maxima > 0.85 or sim_codigo > 0.90:
        originalidad = "Copia modificada"
    elif similitud_maxima > 0.7:
        originalidad = "Inspirado"
    else:
        originalidad = "Original"
    
    return originalidad, similitud_maxima

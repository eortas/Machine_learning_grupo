"""
Funciones para descargar y procesar notebooks oficiales
"""
import urllib.request
import ssl
import json


def descargar_notebook_oficial(url):
    """
    Descarga el notebook oficial desde la URL proporcionada.
    
    Args:
        url: URL del notebook oficial
        
    Returns:
        dict: Notebook en formato JSON o None si falla
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


def extraer_contenido_notebook(notebook):
    """
    Extrae el código y markdown de un notebook.
    
    Args:
        notebook: Notebook en formato JSON
        
    Returns:
        dict: Diccionario con 'codigo' y 'markdown'
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


def extraer_codigo_ejecutable(notebook):
    """
    Extrae solo las líneas de código ejecutable, sin comentarios ni markdown.
    
    Args:
        notebook: Notebook en formato JSON
        
    Returns:
        str: Código ejecutable concatenado
    """
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

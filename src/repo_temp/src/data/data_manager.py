"""
Funciones para gestionar datos de entregas y evaluaciones
Versión corregida que guarda el CSV dentro del repositorio
"""
import os
import pandas as pd


def guardar_evaluacion(nombre, capitulo, fecha, originalidad, similitud, evaluacion_ia, repo_dir):
    """
    Guarda la evaluación completa en un archivo CSV dentro del repositorio.
    
    Args:
        nombre: Nombre del estudiante
        capitulo: Nombre del capítulo
        fecha: Fecha de entrega
        originalidad: Nivel de originalidad
        similitud: Puntuación de similitud
        evaluacion_ia: Diccionario con la evaluación de IA
        repo_dir: Directorio del repositorio donde guardar el CSV
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
    
    # Guardar en el repositorio para que se suba a GitHub
    csv_path = os.path.join(repo_dir, "evaluaciones", "evaluacion_originalidad.csv")
    
    # Crear carpeta evaluaciones si no existe
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    try:
        df_eval = pd.read_csv(csv_path)
        df_eval = pd.concat([df_eval, pd.DataFrame([fila])], ignore_index=True)
    except:
        df_eval = pd.DataFrame([fila])
    
    df_eval.to_csv(csv_path, index=False, encoding='utf-8')
    
    print(f"✅ Evaluación guardada en: {csv_path}")


def generar_hall_of_fame(capitulo, repo_dir):
    """
    Genera el Hall of Fame con los mejores trabajos del capítulo.
    
    Args:
        capitulo: Nombre del capítulo
        repo_dir: Directorio del repositorio
        
    Returns:
        dict: Diccionario con 'mejor', 'creativo', 'explicativo' (si hay suficientes entregas)
    """
    csv_path = os.path.join(repo_dir, "evaluaciones", "evaluacion_originalidad.csv")
    
    try:
        df_eval = pd.read_csv(csv_path)
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


def cargar_registro(repo_dir, registro_path):
    """
    Carga el archivo de registro de entregas.
    
    Args:
        repo_dir: Directorio del repositorio
        registro_path: Ruta relativa del archivo de registro
        
    Returns:
        pd.DataFrame: DataFrame con el registro o None si no existe
    """
    full_path = os.path.join(repo_dir, registro_path)
    if os.path.exists(full_path):
        return pd.read_csv(full_path, encoding="utf-8")
    return None


def actualizar_registro(df, nombre, columna, repo_dir, registro_path):
    """
    Actualiza el registro de entregas marcando como entregado.
    
    Args:
        df: DataFrame con el registro
        nombre: Nombre del estudiante
        columna: Columna del capítulo a actualizar
        repo_dir: Directorio del repositorio
        registro_path: Ruta relativa del archivo de registro
    """
    df.loc[df["Nombre"].str.lower() == nombre, columna] = "✅"
    full_path = os.path.join(repo_dir, registro_path)
    df.to_csv(full_path, index=False, encoding='utf-8')

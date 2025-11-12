"""
Sistema de cierre de capítulo - Versión Simple
Solo cambia los ✅ a emojis especiales para los ganadores del Hall of Fame
"""
import os
import pandas as pd
from datetime import datetime
import pytz


def generar_hall_of_fame_final(capitulo, repo_dir):
    """
    Genera el Hall of Fame con hasta 4 categorías de ganadores.
    Se adapta al número de entregas disponibles.
    
    Args:
        capitulo: Nombre del capítulo
        repo_dir: Directorio del repositorio
        
    Returns:
        dict: {'mejor': 'nombre', 'documentado': 'nombre', 'explorador': 'nombre', 'modelador': 'nombre'}
              Puede tener 1, 2, 3 o 4 categorías según entregas disponibles
    """
    csv_path = os.path.join(repo_dir, "evaluaciones", "evaluacion_originalidad.csv")
    
    try:
        df_eval = pd.read_csv(csv_path)
        df_cap = df_eval[df_eval["Capítulo"] == capitulo].copy()
    except FileNotFoundError:
        return {}
    
    if df_cap.empty:
        return {}
    
    # Filtra copias
    df_validos = df_cap[~df_cap["Originalidad"].isin(["Copia directa", "Copia modificada"])].copy()
    
    # Si no hay entregas válidas, no hay Hall of Fame
    if len(df_validos) == 0:
        return {}
    
    # Calcula puntuación combinada para "mejor trabajo"
    df_validos["Puntuacion_Combinada"] = (
        (1 - df_validos["Similitud"]) * 0.3 + 
        (df_validos["Nota_Total"] / 10) * 0.7
    )
    
    hall = {}
    nombres_usados = []
    
    # 1. 🏆 Mejor trabajo general (siempre se asigna si hay al menos 1 entrega)
    mejor = df_validos.nlargest(1, "Puntuacion_Combinada").iloc[0]
    hall["mejor"] = mejor["Nombre"].lower()
    nombres_usados.append(hall["mejor"])
    
    # 2. 📝 Mejor documentado (si hay al menos 2 entregas)
    df_temp = df_validos[~df_validos["Nombre"].str.lower().isin(nombres_usados)]
    if len(df_temp) > 0:
        documentado = df_temp.nlargest(1, "Documentacion").iloc[0]
        hall["documentado"] = documentado["Nombre"].lower()
        nombres_usados.append(hall["documentado"])
    
    # 3. 🔍 Mejor exploración (si hay al menos 3 entregas)
    df_temp = df_validos[~df_validos["Nombre"].str.lower().isin(nombres_usados)]
    if len(df_temp) > 0:
        explorador = df_temp.nlargest(1, "Exploracion").iloc[0]
        hall["explorador"] = explorador["Nombre"].lower()
        nombres_usados.append(hall["explorador"])
    
    # 4. 🤖 Mejores modelos (si hay al menos 4 entregas)
    df_temp = df_validos[~df_validos["Nombre"].str.lower().isin(nombres_usados)]
    if len(df_temp) > 0:
        modelador = df_temp.nlargest(1, "Modelos").iloc[0]
        hall["modelador"] = modelador["Nombre"].lower()
        nombres_usados.append(hall["modelador"])
    
    return hall


def asignar_emojis_ganadores(capitulo, columna, repo_dir, registro_path):
    """
    Cambia los ✅ de los ganadores por sus emojis especiales.
    El resto de alumnos mantiene su ✅ o ❌.
    
    Args:
        capitulo: Nombre del capítulo
        columna: Columna en el registro
        repo_dir: Directorio del repositorio
        registro_path: Ruta al registro de entregas
        
    Returns:
        tuple: (cambios_realizados, hall_of_fame)
    """
    # Carga registro
    full_path = os.path.join(repo_dir, registro_path)
    if not os.path.exists(full_path):
        return 0, {}
    
    df_registro = pd.read_csv(full_path, encoding="utf-8")
    
    # Genera Hall of Fame
    hall = generar_hall_of_fame_final(capitulo, repo_dir)
    
    if not hall:
        return 0, {}
    
    # Mapeo de categoría a emoji
    emojis = {
        "mejor": "🏆",
        "documentado": "📝",
        "explorador": "🔍",
        "modelador": "🤖"
    }
    
    cambios = 0
    
    # Actualiza solo los ganadores
    for idx, row in df_registro.iterrows():
        nombre = row["Nombre"].lower()
        estado_actual = row[columna]
        
        # Solo actualiza si tiene ✅ (es decir, entregó)
        if estado_actual == "✅":
            # Verifica si es ganador
            for categoria, nombre_ganador in hall.items():
                if nombre == nombre_ganador:
                    emoji = emojis[categoria]
                    df_registro.at[idx, columna] = emoji
                    cambios += 1
                    break
    
    # Guarda registro actualizado
    if cambios > 0:
        df_registro.to_csv(full_path, index=False, encoding='utf-8')
    
    return cambios, hall


def cerrar_capitulo_simple(capitulo, columna, repo_dir, registro_path, fecha_limite):
    """
    Cierra el capítulo y asigna emojis especiales solo a los ganadores.
    Se adapta al número de entregas disponibles.
    
    Args:
        capitulo: Nombre del capítulo
        columna: Columna en el registro
        repo_dir: Directorio del repositorio
        registro_path: Ruta al registro
        fecha_limite: Fecha límite del capítulo
        
    Returns:
        dict: Resumen de la operación
    """
    print(f"\n{'='*80}")
    print(f"🔒 CIERRE DE CAPÍTULO: {capitulo}")
    print(f"{'='*80}\n")
    
    # Verifica que pasó la fecha límite
    madrid_tz = pytz.timezone('Europe/Madrid')
    ahora = datetime.now(madrid_tz)
    if ahora < fecha_limite:
        dias_restantes = (fecha_limite - ahora).days
        return {
            "error": f"El plazo no ha terminado. Faltan {dias_restantes} días.",
            "puede_cerrar": False
        }
    
    # Asigna emojis a ganadores
    print("🏆 Asignando emojis a los ganadores del Hall of Fame...")
    cambios, hall = asignar_emojis_ganadores(capitulo, columna, repo_dir, registro_path)
    
    if cambios == 0:
        print("   ⚠️  No hay entregas válidas para generar Hall of Fame")
        print("   (Todas las entregas son copias o no hay entregas)")
        return {
            "exito": False,
            "error": "No hay entregas válidas para premiar"
        }
    else:
        print(f"   ✅ Se asignaron {cambios} emoji(s) especial(es)\n")
    
    # Muestra ganadores
    print("🌟 HALL OF FAME:\n")
    
    categorias = {
        "mejor": "🏆 Mejor trabajo general",
        "documentado": "📝 Mejor documentado",
        "explorador": "🔍 Mejor exploración",
        "modelador": "🤖 Mejores modelos"
    }
    
    for categoria, descripcion in categorias.items():
        if categoria in hall:
            print(f"   {descripcion}: {hall[categoria].title()}")
    
    # Información sobre categorías no asignadas
    categorias_faltantes = len(categorias) - len(hall)
    if categorias_faltantes > 0:
        print(f"\n   ℹ️  {categorias_faltantes} categoría(s) no asignada(s) por falta de entregas")
    
    print(f"\n{'='*80}")
    print(f"✅ Capítulo cerrado exitosamente")
    print(f"   • {cambios} ganador(es) identificado(s)")
    print(f"   • El resto mantiene su ✅ o ❌")
    print(f"{'='*80}\n")
    
    return {
        "exito": True,
        "cambios": cambios,
        "hall_of_fame": hall,
        "fecha_cierre": ahora.strftime("%Y-%m-%d %H:%M:%S")
    }


def verificar_cierre_automatico(capitulo, columna, repo_dir, registro_path, fecha_limite):
    """
    Verifica si debe cerrarse automáticamente el capítulo.
    
    Args:
        (mismos que cerrar_capitulo_simple)
        
    Returns:
        bool: True si se cerró automáticamente
    """
    

    madrid_tz = pytz.timezone('Europe/Madrid')
    ahora = datetime.now(madrid_tz)
    
    # Solo cierra si pasó la fecha límite
    if ahora <= fecha_limite:
        return False
    
    # Verifica si ya se cerró (comprobando si hay emojis especiales)
    full_path = os.path.join(repo_dir, registro_path)
    if not os.path.exists(full_path):
        return False
    
    df = pd.read_csv(full_path, encoding="utf-8")
    
    # Si ya tiene emojis del Hall of Fame, ya se cerró
    emojis_hall = ["🏆", "📝", "🔍", "🤖"]
    valores = df[columna].values
    
    if any(v in emojis_hall for v in valores if pd.notna(v)):
        # Ya se cerró antes
        return False
    
    # Cierra automáticamente
    print("⚠️  Plazo vencido. Cerrando capítulo automáticamente...")
    resultado = cerrar_capitulo_simple(capitulo, columna, repo_dir, registro_path, fecha_limite)
    
    return resultado.get("exito", False)

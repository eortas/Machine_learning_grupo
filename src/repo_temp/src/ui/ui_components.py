"""
Componentes de la interfaz de usuario con Streamlit
Versión actualizada con soporte para emojis del Hall of Fame
"""
import streamlit as st
from datetime import datetime
import pytz


def mostrar_header(capitulo, fecha_limite):
    """
    Muestra el encabezado con el título y el contador de días.
    
    Args:
        capitulo: Nombre del capítulo
        fecha_limite: Fecha límite de entrega
    """
    madrid_tz = pytz.timezone('Europe/Madrid')
    hoy = datetime.now(madrid_tz)
    dias_restantes = (fecha_limite - hoy).days
    
    st.title(f"Subida de prácticas - {capitulo}")
    
    if dias_restantes > 1:
        st.info(f"Quedan **{dias_restantes} días** para entregar la práctica.")
    elif dias_restantes == 1:
        st.warning("⚠️ ¡Mañana es el último día para entregar la práctica!")
    elif dias_restantes == 0:
        st.error("🚨 La entrega cierra hoy.")
    else:
        st.error("❌ El plazo de entrega ha finalizado. No se pueden subir más archivos.")
        st.stop()
    
    st.caption(f"Fecha límite: {fecha_limite.strftime('%d/%m/%Y a las %H:%M')}")



def mostrar_resultado_originalidad(originalidad, similitud):
    """
    Muestra el resultado de la evaluación de originalidad.
    
    Args:
        originalidad: Nivel de originalidad
        similitud: Puntuación de similitud (0.0 a 1.0)
    """
    if originalidad == "Copia directa":
        st.error(f"🚫 **COPIA DIRECTA DETECTADA** (Similitud: {similitud*100:.1f}%)")
        st.warning("Tu notebook es idéntico al oficial. No se evaluará.")
    elif originalidad == "Copia modificada":
        st.warning(f"⚠️ **Copia con modificaciones** (Similitud: {similitud*100:.1f}%)")
    elif originalidad == "Inspirado":
        st.info(f"💡 **Trabajo inspirado** (Similitud: {similitud*100:.1f}%)")
    else:
        st.success(f"🎉 **Trabajo original** (Similitud: {similitud*100:.1f}%)")


def mostrar_evaluacion_ia(evaluacion_ia, originalidad):
    """
    Muestra la evaluación completa de IA.
    
    Args:
        evaluacion_ia: Diccionario con la evaluación
        originalidad: Nivel de originalidad del trabajo
    """
    if evaluacion_ia["nota_total"] == 0:
        return
    
    st.markdown("---")
    st.subheader("📊 Evaluación Automática con IA")
    
    # Nota principal
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


def mostrar_tabla_entregas(df, columna, hall):
    """
    Muestra la tabla de entregas con emojis según el Hall of Fame.
    
    Args:
        df: DataFrame con el registro de entregas
        columna: Columna del capítulo actual
        hall: Diccionario del Hall of Fame
    """
    def marcar_entrega(nombre, estado):
        """
        Determina el emoji a mostrar según el estado y Hall of Fame.
        
        Prioridad:
        1. Si ya tiene emoji especial del cierre (🏆📝🔍🤖), mantenerlo
        2. Si aún no se cerró, usar Hall of Fame temporal
        3. Si no está en Hall of Fame, usar ✅ o ❌
        """
        # Si ya tiene emoji especial del cierre, lo mantine
        emojis_especiales = ["🏆", "📝", "🔍", "🤖"]
        if estado in emojis_especiales:
            return estado
        
        # Si no está cerrado aún, usa la lógica temporal del Hall of Fame
        nombre = nombre.lower()
        if estado == "✅":
            # Verificar si está en el Hall of Fame temporal
            if hall.get("mejor") == nombre:
                return "🏆"
            elif hall.get("documentado") == nombre:
                return "📝"
            elif hall.get("explorador") == nombre:
                return "🔍"
            elif hall.get("modelador") == nombre:
                return "🤖"
            else:
                return "✅"
        return "❌"
    
    df_show = df.copy().fillna("❌")
    df_show[columna] = df_show.apply(
        lambda row: marcar_entrega(row["Nombre"], row[columna]), 
        axis=1
    )
    
    st.subheader("Listado de miembros y estado de entregas")
    st.dataframe(df_show, use_container_width=True)
    
    # Leyenda de emojis
    with st.expander("📘 ¿Qué significan los emojis?"):
        st.markdown("""
        **Emojis del Hall of Fame:**
        - 🏆 **Mejor trabajo general**: Mayor puntuación combinada (originalidad + nota IA)
        - 📝 **Mejor documentado**: Mejor documentación y explicaciones
        - 🔍 **Mejor exploración**: Mejor análisis exploratorio de datos
        - 🧐 **Mejores modelos**: Mejor implementación de modelos ML
        
        **Emojis de estado:**
        - ✅ **Entrega válida**: Práctica subida correctamente
        - ❌ **No entregado**: Sin práctica subida
        
        *Nota: Los emojis especiales (🏆📝🔍🧐) se asignan al cerrar el capítulo.*
        """)


def mostrar_mensaje_exito(archivo_nombre, archivo_autor, similitud):
    """
    Muestra el mensaje de éxito después de completar la entrega.
    
    Args:
        archivo_nombre: Nombre del archivo subido
        archivo_autor: Autor del archivo
        similitud: Puntuación de similitud
    """
    st.markdown("---")
    st.markdown(f"""
    ### 🎉 Entrega completada
    
    - **Archivo:** `{archivo_nombre}`  
    - **Autor:** `{archivo_autor}`  
    - **Similitud:** `{similitud*100:.1f}%`
    - **Estado:** ✅ Registro actualizado
    
    🙌 ¡Gracias por tu participación en nuestra comunidad!
    """)
    

from datetime import datetime
import streamlit as st
import pytz

# Configuración del capítulo (cambia en cada entrega)
CAPITULO = "Capítulo 2"
COLUMNA = "Capítulo 2"
CARPETA_DESTINO = "capitulo_02"
FECHA_LIMITE = pytz.timezone('Europe/Madrid').localize(datetime(2025, 11, 24, 20, 30, 0))

# Configuración del repositorio GitHub
REPO_URL = "https://github.com/eortas/Machine_learning_grupo.git"
REPO_DIR = "repo_temp"
REGISTRO_PATH = "uploads/registro_entregas.csv"

# URL del notebook oficial 
SOLUCION_OFICIAL_URL = "https://github.com/ageron/handson-ml3/raw/main/02_end_to_end_machine_learning_project.ipynb"

# Carga tokens desde secrets
try:
    TOKEN = st.secrets.get("GITHUB_TOKEN", "")
    GROQ_API_KEY = st.secrets.get("GROQ_API_KEY", "")
except:
    TOKEN = ""
    GROQ_API_KEY = ""

# Enunciado del ejercicio
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

# Sistema de Entregas de Prácticas ML

Sistema automatizado para gestionar entregas de prácticas de Machine Learning con evaluación automática de originalidad y calidad mediante IA.

## 📁 Estructura del Proyecto

```
.
├── app.py                          # Aplicación principal de Streamlit
├── config.py                       # Configuración y constantes
├── git_manager.py                  # Gestión del repositorio Git
├── data_manager.py                 # Gestión de datos y CSV
├── validators.py                   # Validación de archivos y nombres
├── file_processor.py               # Procesamiento de archivos ZIP
├── notebook_utils.py               # Utilidades para notebooks
├── evaluacion_originalidad.py      # Evaluación de originalidad
├── evaluacion_ia.py                # Evaluación con IA (Groq)
├── ui_components.py                # Componentes de interfaz
└── README.md                       # Este archivo
```

🧠 ML Practice Evaluator

ML Practice Evaluator es una plataforma interactiva que automatiza la evaluación de prácticas de Machine Learning, combinando análisis de originalidad y valoración cualitativa mediante inteligencia artificial.

🚀 Descripción general

El sistema recibe entregas de notebooks, valida su formato y las analiza comparándolas con soluciones oficiales.
Cada práctica se evalúa en dos dimensiones:

Originalidad: detección de similitudes con la solución base y penalización por coincidencias excesivas.

Calidad técnica: valoración automática con IA (API de Groq) en cinco criterios —exploración, preprocesamiento, modelado, análisis y documentación—.

Los resultados se registran y visualizan en un panel interactivo (Streamlit), que incluye un historial de envíos y un ranking dinámico de las mejores prácticas.

⚙️ Funcionamiento

El proyecto se estructura en módulos que actúan de forma coordinada:

Validación de entregas y formato de archivos.

Procesamiento y extracción de notebooks desde archivos ZIP.

Evaluación automática mediante comparación de código y análisis semántico con IA.

Registro y actualización de resultados en un repositorio Git.

Visualización de métricas, evaluaciones y clasificaciones en tiempo real.

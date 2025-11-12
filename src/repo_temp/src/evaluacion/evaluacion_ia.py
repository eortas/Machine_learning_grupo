"""
Funciones para evaluar notebooks usando IA (Groq)
Versión mejorada con evaluación más estricta
CORREGIDO v2: La nota es SIEMPRE la suma de componentes, sin penalizaciones posteriores
"""
import json
import time
import requests
import streamlit as st
from config.settings import GROQ_API_KEY, ENUNCIADO_EJERCICIO
from utils.notebook_utils import extraer_contenido_notebook


def evaluar_con_groq(notebook_usuario):
    """
    Evalúa un notebook usando la API de Groq con criterios más estrictos.
    
    Args:
        notebook_usuario: Notebook del estudiante en formato JSON
        
    Returns:
        dict: Evaluación con nota y comentarios, o None si falla
    """
    if not GROQ_API_KEY:
        return None
    
    contenido = extraer_contenido_notebook(notebook_usuario)
    
    # Usa TODO el contenido sin limitaciones de tokens
    codigo = contenido["codigo"]
    markdown = contenido["markdown"]
    
    prompt = f"""Eres un profesor ESTRICTO y EXIGENTE de Machine Learning evaluando la práctica de un estudiante. 

**IMPORTANTE: Sé muy crítico y exigente. Un aprobado (5.0) debe demostrar dominio real de los conceptos.**

**ENUNCIADO DEL EJERCICIO:**
{ENUNCIADO_EJERCICIO}

**NOTEBOOK DEL ESTUDIANTE:**

CÓDIGO:
```python
{codigo}
```

EXPLICACIONES (MARKDOWN):
{markdown}

**CRITERIOS DE EVALUACIÓN ESTRICTOS:**

1. **Exploración de datos (0-2 puntos)**
   - 0.0-0.5: Solo carga datos o visualización básica
   - 0.6-1.0: Análisis descriptivo básico (shape, info, describe)
   - 1.1-1.5: Análisis de correlaciones, distribuciones y valores faltantes
   - 1.6-2.0: Análisis profundo con visualizaciones múltiples e insights valiosos

2. **Preprocesamiento (0-2 puntos)**
   - 0.0: No hay preprocesamiento o está incompleto/incorrecto
   - 0.5-1.0: Train/test split básico solamente
   - 1.1-1.5: Pipeline básico con manejo de nulos y escalado
   - 1.6-2.0: Pipeline completo con transformadores personalizados y encoders

3. **Modelos implementados (0-3 puntos)**
   - 0.0: No hay modelos implementados
   - 0.5-1.0: Un solo modelo sin validación cruzada
   - 1.1-2.0: Al menos 2 modelos con evaluación básica
   - 2.1-3.0: Múltiples modelos con validación cruzada e hiperparámetros optimizados

4. **Evaluación y análisis (0-2 puntos)**
   - 0.0: No hay evaluación de modelos
   - 0.5-1.0: Métricas básicas sin análisis
   - 1.1-1.5: Comparación de modelos con varias métricas
   - 1.6-2.0: Análisis profundo de errores y visualizaciones de predicciones

5. **Documentación (0-1 punto)**
   - 0.0-0.3: Sin explicaciones o muy básicas
   - 0.4-0.6: Explicaciones mínimas de los pasos
   - 0.7-1.0: Documentación clara con conclusiones y análisis

**INSTRUCCIONES CRÍTICAS:**
- Solo da nota >= 5.0 si hay REALMENTE un modelo de ML implementado y evaluado
- Si no hay modelos implementados, la nota máxima es 3.0 (solo exploración)
- Si no hay preprocesamiento adecuado, la nota máxima es 4.0
- Si el código tiene muchos errores o no se ejecutaría, penaliza fuertemente
- NO seas paternalista. Si el trabajo está incompleto, debe suspender.

**IMPORTANTE: LA NOTA TOTAL DEBE SER LA SUMA EXACTA DE LOS 5 COMPONENTES**

Devuelve tu respuesta en este formato JSON exacto:
{{
    "nota_total": 2.5,
    "exploracion": 1.2,
    "preprocesamiento": 0.0,
    "modelos": 0.0,
    "evaluacion": 0.0,
    "documentacion": 0.3,
    "comentario": "El estudiante solo ha realizado carga y visualización muy básica de datos. No hay preprocesamiento, modelos ni evaluación. Trabajo muy incompleto que no cumple los objetivos mínimos del ejercicio.",
    "puntos_fuertes": ["Carga correcta de datos"],
    "areas_mejora": ["Implementar preprocesamiento completo", "Desarrollar e implementar modelos de ML", "Realizar evaluación y análisis de resultados", "Mejorar documentación"]
}}

RECUERDA: 
- Nota < 3.0 si solo hay carga/exploración básica de datos
- Nota 3.0-4.0 si hay exploración completa pero sin modelos
- Nota 5.0+ SOLO si hay modelos implementados y funcionando
- Nota 7.0+ requiere trabajo excelente en todas las áreas
- LA NOTA TOTAL = exploracion + preprocesamiento + modelos + evaluacion + documentacion"""

    max_intentos = 3
    ultimo_error = None
    
    for intento in range(max_intentos):
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "Eres un profesor universitario ESTRICTO de Machine Learning. NO seas condescendiente. Evalúa con rigor académico real."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1000
                },
                timeout=60
            )
            
            if response.status_code == 200:
                try:
                    resultado = response.json()
                    contenido_respuesta = resultado["choices"][0]["message"]["content"]
                    
                    # Extrae JSON de la respuesta
                    inicio = contenido_respuesta.find('{')
                    fin = contenido_respuesta.rfind('}') + 1
                    
                    if inicio != -1 and fin > inicio:
                        json_str = contenido_respuesta[inicio:fin]
                        evaluacion = json.loads(json_str)
                        
                        # ============ CORRECCIÓN DEFINITIVA ============
                        # LA NOTA TOTAL SIEMPRE ES LA SUMA DE LOS COMPONENTES
                        # No hay penalizaciones posteriores
                        nota_calculada = (
                            evaluacion.get("exploracion", 0) +
                            evaluacion.get("preprocesamiento", 0) +
                            evaluacion.get("modelos", 0) +
                            evaluacion.get("evaluacion", 0) +
                            evaluacion.get("documentacion", 0)
                        )
                        
                        # Redondea a 1 decimal
                        evaluacion["nota_total"] = round(nota_calculada, 1)
                        # =============================================
                        
                        return evaluacion
                    else:
                        ultimo_error = "No se encontró JSON en la respuesta"
                        continue
                        
                except json.JSONDecodeError as e:
                    ultimo_error = f"Error al parsear JSON: {str(e)}"
                    continue
                except KeyError as e:
                    ultimo_error = f"Error en estructura de respuesta: {str(e)}"
                    continue
                    
            elif response.status_code == 429:
                if intento < max_intentos - 1:
                    tiempo_espera = (intento + 1) * 30
                    time.sleep(tiempo_espera)
                    continue
                else:
                    ultimo_error = "Rate limit excedido"
                    
            else:
                ultimo_error = f"Error HTTP {response.status_code}: {response.text[:200]}"
                continue
                
        except requests.exceptions.Timeout:
            ultimo_error = "Timeout en Groq"
            if intento < max_intentos - 1:
                time.sleep(5)
                continue
        except Exception as e:
            ultimo_error = f"Error general: {str(e)}"
            continue
    
    # Si llegamos aquí, falló todo
    return None


def evaluar_respuestas_ia(notebook_usuario):
    """
    Función principal de evaluación con IA.
    Intenta usar Groq y retorna evaluación por defecto si falla.
    
    Args:
        notebook_usuario: Notebook del estudiante en formato JSON
        
    Returns:
        dict: Evaluación completa
    """
    evaluacion = evaluar_con_groq(notebook_usuario)
    
    if evaluacion:
        return evaluacion
    
    # Si falla, devuelve la evaluación por defecto MÁS BAJA
    return {
        "nota_total": 3.0,
        "exploracion": 0.5,
        "preprocesamiento": 0.0,
        "modelos": 0.0,
        "evaluacion": 0.0,
        "documentacion": 0.5,
        "comentario": "No se pudo evaluar automáticamente. Revisión manual necesaria. Nota provisional baja hasta confirmación.",
        "puntos_fuertes": ["Archivo subido correctamente"],
        "areas_mejora": ["Requiere revisión manual completa"]
    }
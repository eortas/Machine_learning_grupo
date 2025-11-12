"""
Funciones para evaluar notebooks usando IA (Groq)
Versión mejorada con evaluación más estricta
CON SOPORTE PARA MÚLTIPLES API KEYS (FALLBACK)
"""
import json
import time
import requests
import streamlit as st
from config.settings import ENUNCIADO_EJERCICIO
from utils.notebook_utils import extraer_contenido_notebook


def evaluar_con_groq(notebook_usuario):
    """
    Evalúa un notebook usando la API de Groq con criterios más estrictos.
    Soporta múltiples API keys por si una falla.
    
    Args:
        notebook_usuario: Notebook del estudiante en formato JSON
        
    Returns:
        dict: Evaluación con nota y comentarios, o None si falla
    """
    # Obtener ambas API keys
    groq_api_key_1 = st.secrets.get("GROQ_API_KEY", "")
    groq_api_key_2 = st.secrets.get("GROQ_API_KEY_2", "")  # Segunda clave (si existe)
    
    api_keys = [groq_api_key_1]
    if groq_api_key_2:
        api_keys.append(groq_api_key_2)
    
    st.error(f"DEBUG: Encontradas {len(api_keys)} API keys")
    
    if not api_keys or not api_keys[0]:
        st.error("❌ No hay API keys de Groq configuradas")
        return None
    
    contenido = extraer_contenido_notebook(notebook_usuario)
    
    # Usa TODO el contenido sin limitaciones de tokens
    codigo = contenido["codigo"]
    markdown = contenido["markdown"]
    
    st.error(f"DEBUG: Tamaño del código: {len(codigo)} chars, markdown: {len(markdown)} chars")
    
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
    "comentario": "El estudiante solo ha realizado carga y visualización muy básica de datos.",
    "puntos_fuertes": ["Carga correcta de datos"],
    "areas_mejora": ["Implementar preprocesamiento completo"]
}}"""

    # Intentar con cada API key
    for idx, api_key in enumerate(api_keys, 1):
        st.error(f"🔄 Intentando con API key #{idx}...")
        resultado = _intentar_con_api_key(api_key, prompt, idx)
        
        if resultado:
            return resultado
        
        if idx < len(api_keys):
            st.error(f"❌ API key #{idx} falló. Intentando con API key #{idx+1}...")
        else:
            st.error(f"❌ API key #{idx} también falló. Sin más claves disponibles.")
    
    # Si llegamos aquí, todas las API keys fallaron
    st.error("❌ TODAS las API keys de Groq han fallado. Intenta más tarde.")
    return None


def _intentar_con_api_key(api_key, prompt, num_key):
    """
    Intenta evaluar con una API key específica.
    
    Args:
        api_key: API key de Groq
        prompt: Prompt para la evaluación
        num_key: Número de la clave (para debug)
        
    Returns:
        dict: Evaluación si tiene éxito, None si falla
    """
    max_intentos = 2
    
    for intento in range(max_intentos):
        try:
            st.error(f"DEBUG: Intento {intento+1} con API key #{num_key}")
            
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
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
            
            st.error(f"DEBUG: Status code = {response.status_code}")
            
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
                        nota_calculada = (
                            evaluacion.get("exploracion", 0) +
                            evaluacion.get("preprocesamiento", 0) +
                            evaluacion.get("modelos", 0) +
                            evaluacion.get("evaluacion", 0) +
                            evaluacion.get("documentacion", 0)
                        )
                        
                        evaluacion["nota_total"] = round(nota_calculada, 1)
                        # =============================================
                        
                        st.success("✅ Evaluación exitosa")
                        return evaluacion
                    else:
                        st.error("❌ No se encontró JSON en la respuesta")
                        continue
                        
                except json.JSONDecodeError as e:
                    st.error(f"❌ Error al parsear JSON: {str(e)}")
                    continue
                except KeyError as e:
                    st.error(f"❌ Error en estructura: {str(e)}")
                    continue
                    
            elif response.status_code == 429:
                st.error("🚫 429 - Rate limit excedido en Groq")
                return None
            elif response.status_code == 401:
                st.error(f"🚫 401 - API key inválida o expirada")
                return None
            else:
                error_msg = response.text[:500] if response.text else "Sin detalles"
                st.error(f"❌ Error HTTP {response.status_code}: {error_msg}")
                return None
                
        except requests.exceptions.Timeout:
            st.error("⏱️ Timeout en Groq")
            time.sleep(5)
            continue
        except Exception as e:
            st.error(f"❌ Excepción: {str(e)}")
            continue
    
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
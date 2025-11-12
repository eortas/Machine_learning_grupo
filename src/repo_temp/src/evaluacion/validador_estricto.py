"""
Sistema de validación y penalización estricta para notebooks
"""
import re


def analizar_completitud_notebook(notebook):
    """
    Analiza la completitud real del notebook y aplica penalizaciones.
    
    Args:
        notebook: Notebook en formato JSON
        
    Returns:
        dict: {
            'tiene_modelos': bool,
            'tiene_preprocesamiento': bool,
            'tiene_evaluacion': bool,
            'celdas_ejecutadas': int,
            'tiene_errores': bool,
            'nota_maxima_sugerida': float,
            'razones': list
        }
    """
    analisis = {
        'tiene_modelos': False,
        'tiene_preprocesamiento': False,
        'tiene_evaluacion': False,
        'tiene_train_test_split': False,
        'celdas_ejecutadas': 0,
        'total_celdas': 0,
        'tiene_errores': False,
        'nota_maxima_sugerida': 10.0,
        'razones': []
    }
    
    codigo_completo = []
    
    for cell in notebook.get('cells', []):
        if cell.get('cell_type') == 'code':
            analisis['total_celdas'] += 1
            source = ''.join(cell.get('source', []))
            codigo_completo.append(source)
            
            # Verificar si la celda se ejecutó
            if cell.get('execution_count') is not None:
                analisis['celdas_ejecutadas'] += 1
            
            # Verificar si hay errores en los outputs
            outputs = cell.get('outputs', [])
            for output in outputs:
                if output.get('output_type') == 'error':
                    analisis['tiene_errores'] = True
    
    codigo_texto = '\n'.join(codigo_completo)
    
    # Detectar modelos de ML
    patrones_modelos = [
        r'LinearRegression\(',
        r'RandomForest',
        r'DecisionTree',
        r'GradientBoosting',
        r'XGBoost',
        r'LightGBM',
        r'SVR\(',
        r'KNeighbors',
        r'\.fit\(',  # Método fit es indicativo de entrenamiento
    ]
    
    for patron in patrones_modelos:
        if re.search(patron, codigo_texto):
            analisis['tiene_modelos'] = True
            break
    
    # Detectar preprocesamiento
    patrones_preprocesamiento = [
        r'train_test_split',
        r'StandardScaler',
        r'MinMaxScaler',
        r'Pipeline',
        r'ColumnTransformer',
        r'SimpleImputer',
        r'OneHotEncoder',
        r'LabelEncoder',
    ]
    
    for patron in patrones_preprocesamiento:
        if re.search(patron, codigo_texto):
            analisis['tiene_preprocesamiento'] = True
            break
    
    # Detectar train_test_split específicamente
    if re.search(r'train_test_split', codigo_texto):
        analisis['tiene_train_test_split'] = True
    
    # Detectar evaluación y métricas específicas
    patrones_evaluacion = [
        r'mean_squared_error',
        r'mean_absolute_error',
        r'r2_score',
        r'cross_val_score',
        r'GridSearchCV',
        r'\.score\(',
        r'\.predict\(',
    ]
    
    # Detectar métricas específicas
    metricas_detectadas = []
    metricas_regresion = {
        r'mean_squared_error|MSE': 'MSE/RMSE',
        r'root_mean_squared_error|RMSE': 'RMSE',
        r'mean_absolute_error|MAE': 'MAE',
        r'r2_score|R2|R\^2': 'R²',
        r'mean_absolute_percentage_error|MAPE': 'MAPE',
    }
    
    metricas_clasificacion = {
        r'accuracy_score|accuracy': 'Accuracy',
        r'precision_score|precision': 'Precision',
        r'recall_score|recall': 'Recall',
        r'f1_score|F1': 'F1-Score',
        r'roc_auc_score|AUC': 'ROC-AUC',
        r'confusion_matrix': 'Confusion Matrix',
        r'classification_report': 'Classification Report',
    }
    
    # Buscar métricas en el código
    for patron, nombre in {**metricas_regresion, **metricas_clasificacion}.items():
        if re.search(patron, codigo_texto, re.IGNORECASE):
            metricas_detectadas.append(nombre)
    
    analisis['metricas_detectadas'] = list(set(metricas_detectadas))  # Eliminar duplicados
    
    # Tiene evaluación si usa métricas o métodos de evaluación
    for patron in patrones_evaluacion:
        if re.search(patron, codigo_texto):
            analisis['tiene_evaluacion'] = True
            break
    
    # También contar como evaluación si tiene al menos 2 métricas
    if len(metricas_detectadas) >= 2:
        analisis['tiene_evaluacion'] = True
    
    # Calcular nota máxima sugerida basada en completitud
    if not analisis['tiene_modelos']:
        analisis['nota_maxima_sugerida'] = 3.5
        analisis['razones'].append("Sin modelos de ML implementados")
    
    if not analisis['tiene_preprocesamiento']:
        analisis['nota_maxima_sugerida'] = min(analisis['nota_maxima_sugerida'], 4.0)
        analisis['razones'].append("Sin preprocesamiento adecuado")
    
    if not analisis['tiene_evaluacion'] and analisis['tiene_modelos']:
        analisis['nota_maxima_sugerida'] = min(analisis['nota_maxima_sugerida'], 5.0)
        analisis['razones'].append("Sin evaluación de modelos")
    
    # Penalizar si tiene modelos pero sin métricas específicas
    if analisis['tiene_modelos'] and len(analisis['metricas_detectadas']) == 0:
        analisis['nota_maxima_sugerida'] = min(analisis['nota_maxima_sugerida'], 5.5)
        analisis['razones'].append("Tiene modelos pero sin métricas de evaluación")
    
    # Bonus si tiene múltiples métricas (indica análisis profundo)
    if len(analisis['metricas_detectadas']) >= 3:
        analisis['tiene_analisis_completo'] = True
    else:
        analisis['tiene_analisis_completo'] = False
    
    if analisis['tiene_errores']:
        analisis['nota_maxima_sugerida'] = min(analisis['nota_maxima_sugerida'], 6.0)
        analisis['razones'].append("El código contiene errores de ejecución")
    
    # Penalizar si hay pocas celdas ejecutadas
    if analisis['total_celdas'] > 0:
        porcentaje_ejecucion = analisis['celdas_ejecutadas'] / analisis['total_celdas']
        if porcentaje_ejecucion < 0.3:
            analisis['nota_maxima_sugerida'] = min(analisis['nota_maxima_sugerida'], 4.0)
            analisis['razones'].append("Menos del 30% de celdas ejecutadas")
    
    return analisis


def aplicar_penalizaciones(evaluacion_ia, analisis_completitud):
    """
    Aplica penalizaciones a la evaluación de IA basándose en el análisis de completitud.
    
    Args:
        evaluacion_ia: Dict con la evaluación de IA
        analisis_completitud: Dict con el análisis de completitud
        
    Returns:
        dict: Evaluación ajustada con penalizaciones
    """
    evaluacion_ajustada = evaluacion_ia.copy()
    nota_original = evaluacion_ajustada['nota_total']
    nota_ajustada = min(nota_original, analisis_completitud['nota_maxima_sugerida'])
    
    if nota_ajustada < nota_original:
        # Ajustar nota total
        evaluacion_ajustada['nota_total'] = nota_ajustada
        
        # Actualizar comentario
        razones_texto = "; ".join(analisis_completitud['razones'])
        evaluacion_ajustada['comentario'] = f"⚠️ NOTA AJUSTADA de {nota_original:.1f} a {nota_ajustada:.1f} - {razones_texto}. " + evaluacion_ajustada['comentario']
        
        # Añadir razones a áreas de mejora si no están
        for razon in analisis_completitud['razones']:
            if razon not in evaluacion_ajustada.get('areas_mejora', []):
                evaluacion_ajustada.setdefault('areas_mejora', []).insert(0, razon)
    
    return evaluacion_ajustada


def generar_informe_completitud(analisis):
    """
    Genera un informe legible del análisis de completitud.
    
    Args:
        analisis: Dict con el análisis de completitud
        
    Returns:
        str: Informe en texto
    """
    informe = "📋 **Análisis de Completitud:**\n\n"
    
    if analisis['tiene_modelos']:
        informe += "✅ Modelos de ML detectados\n"
    else:
        informe += "❌ NO se detectaron modelos de ML\n"
    
    if analisis['tiene_preprocesamiento']:
        informe += "✅ Preprocesamiento detectado\n"
    else:
        informe += "❌ NO se detectó preprocesamiento\n"
    
    if analisis['tiene_evaluacion']:
        informe += "✅ Evaluación de modelos detectada\n"
    else:
        informe += "❌ NO se detectó evaluación de modelos\n"
    
    # Mostrar métricas detectadas
    if analisis.get('metricas_detectadas'):
        informe += f"\n📊 **Métricas detectadas ({len(analisis['metricas_detectadas'])}):**\n"
        for metrica in analisis['metricas_detectadas']:
            informe += f"   ✅ {metrica}\n"
        
        if analisis.get('tiene_analisis_completo'):
            informe += "   🌟 Análisis completo con múltiples métricas\n"
    else:
        if analisis['tiene_modelos']:
            informe += "\n⚠️ Tiene modelos pero NO usa métricas de evaluación\n"
    
    if analisis['total_celdas'] > 0:
        porcentaje = (analisis['celdas_ejecutadas'] / analisis['total_celdas']) * 100
        informe += f"\n📈 Celdas ejecutadas: {analisis['celdas_ejecutadas']}/{analisis['total_celdas']} ({porcentaje:.0f}%)\n"
    
    if analisis['tiene_errores']:
        informe += "⚠️ Se detectaron errores de ejecución en el código\n"
    
    if analisis['razones']:
        informe += f"\n🔴 **Nota máxima sugerida: {analisis['nota_maxima_sugerida']:.1f}/10**\n"
        informe += "Razones:\n"
        for razon in analisis['razones']:
            informe += f"  • {razon}\n"
    
    return informe
# C:\Users\nicol\Desktop\DaddyBalance\modulos\asistente_ia.py

def generar_explicacion_renta(resultados, detalle_agregados=None):
    """
    Genera un texto explicativo validando la existencia de columnas.
    """
    utilidad = resultados['resultado_contable']
    agregados = resultados['total_agregados']
    rli = resultados['rli_estimada']
    
    texto = f"El análisis de DaddyBalance indica que la empresa presenta una "
    texto += f"{'Utilidad' if utilidad > 0 else 'Pérdida'} Financiera de $ {abs(utilidad):,.0f}. "
    
    if agregados > 0:
        texto += f"Se han detectado gastos no deducibles por $ {agregados:,.0f}."
        
        # VALIDACIÓN: Solo intentamos listar códigos si la columna existe
        if detalle_agregados is not None and not detalle_agregados.empty:
            if 'Código' in detalle_agregados.columns:
                codigos = [str(c) for c in detalle_agregados['Código'].tolist()]
                texto += f" Específicamente, se identificaron ajustes en las cuentas código: {', '.join(codigos)}."
            else:
                texto += " Se identificaron ajustes en cuentas de gastos rechazados según palabras clave."
            
        texto += f" Esto resulta en una RLI Final de $ {rli:,.0f}. "
        texto += "⚠️ Sugerencia: Estos montos deben ser informados como agregados en el F22."
    else:
        texto += " No se detectaron gastos rechazados automáticos en este balance."
        
    return texto
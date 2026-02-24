# C:\Users\nicol\Desktop\DaddyBalance\modulos\asistente_ia.py

def _normalizar_nombre_columna(nombre):
    """Normaliza nombre de columna (mayúsculas, sin tildes) para comparar con CODIGO."""
    s = str(nombre).strip().upper()
    for viejo, nuevo in [("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U")]:
        s = s.replace(viejo, nuevo)
    return s


def _columna_codigo_en_dataframe(df):
    """Devuelve el nombre real de la columna que equivale a CODIGO, o None."""
    if df is None or df.empty:
        return None
    for c in df.columns:
        if _normalizar_nombre_columna(c) == "CODIGO":
            return c
    return None


def generar_explicacion_renta(resultados, detalle_agregados=None):
    """
    Genera un texto explicativo validando la existencia de columnas.
    Usa búsqueda flexible de columna código (CODIGO, Código, etc.).
    """
    utilidad = resultados["resultado_contable"]
    agregados = resultados["total_agregados"]
    rli = resultados["rli_estimada"]

    texto = "El análisis de DaddyBalance indica que la empresa presenta una "
    texto += f"{'Utilidad' if utilidad > 0 else 'Pérdida'} Financiera de $ {abs(utilidad):,.0f}. "

    if agregados > 0:
        texto += f"Se han detectado gastos no deducibles por $ {agregados:,.0f}."

        col_codigo = _columna_codigo_en_dataframe(detalle_agregados)
        if col_codigo:
            codigos = [str(c) for c in detalle_agregados[col_codigo].dropna().tolist()]
            if codigos:
                texto += f" Específicamente, se identificaron ajustes en las cuentas código: {', '.join(codigos)}."
            else:
                texto += " Se identificaron ajustes en cuentas de gastos rechazados según palabras clave."
        else:
            texto += " Se identificaron ajustes en cuentas de gastos rechazados según palabras clave."

        texto += f" Esto resulta en una RLI Final de $ {rli:,.0f}. "
        texto += "⚠️ Sugerencia: Estos montos deben ser informados como agregados en el F22."
    else:
        texto += " No se detectaron gastos rechazados automáticos en este balance."

    return texto

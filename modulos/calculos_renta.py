from modulos.lector_contable import detectar_gastos_rechazados


def calcular_rli_basica(df, regimen="Propyme General (14 D3)", patrones=None):
    """
    patrones: lista de patrones de gastos rechazados; si es None, se usa config (secrets o default).
    """
    total_perdida = df['PERDIDA'].sum() if 'PERDIDA' in df.columns else 0
    total_ganancia = df['GANANCIA'].sum() if 'GANANCIA' in df.columns else 0

    resultado_contable = total_ganancia - total_perdida

    gastos_rechazados = detectar_gastos_rechazados(df, patrones=patrones)
    total_agregados = 0
    if not gastos_rechazados.empty and "PERDIDA" in gastos_rechazados.columns:
        total_agregados = gastos_rechazados["PERDIDA"].sum()

    rli_estimada = resultado_contable + total_agregados

    tasa = 0.10 if "D3" in regimen else 0
    impuesto = rli_estimada * tasa

    return {
        "resultado_contable": resultado_contable,
        "total_agregados": total_agregados,
        "rli_estimada": rli_estimada,
        "impuesto_pagar": impuesto,
        "tasa_aplicada": tasa
    }

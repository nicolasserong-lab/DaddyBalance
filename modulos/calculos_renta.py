def calcular_rli_basica(df, regimen="Propyme General (14 D3)"):

    total_perdida = df['PERDIDA'].sum() if 'PERDIDA' in df.columns else 0
    total_ganancia = df['GANANCIA'].sum() if 'GANANCIA' in df.columns else 0

    resultado_contable = total_ganancia - total_perdida

    # Gastos rechazados (si existe columna)
    total_agregados = 0
    if 'PERDIDA' in df.columns and 'CUENTA' in df.columns:
        gastos_rechazados = df[df['CUENTA'].str.contains('MULTA|INTERESES', case=False, na=False)]
        total_agregados = gastos_rechazados['PERDIDA'].sum()

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

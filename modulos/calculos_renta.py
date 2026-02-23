# C:\Users\nicol\Desktop\DaddyBalance\modulos\calculos_renta.py

def calcular_rli_basica(df):
    """
    Calcula la RLI buscando las columnas por nombre para evitar errores.
    """
    try:
        # Convertimos los nombres de las columnas a mayúsculas para comparar fácil
        df.columns = [str(c).upper().strip() for c in df.columns]
        
        # 1. Identificar columnas clave (Pérdidas y Ganancias)
        # En Chile se suelen llamar 'PÉRDIDA' y 'GANANCIA' o similar
        col_perdida = next((c for c in df.columns if 'PÉRDIDA' in c or 'PERDIDA' in c or 'DÉBITO' in c), None)
        col_ganancia = next((c for c in df.columns if 'GANANCIA' in c or 'CRÉDITO' in c), None)

        if not col_perdida or not col_ganancia:
             return "Error: No se encontraron columnas de montos (Pérdida/Ganancia)."

        # 2. Resultado Financiero
        total_perdidas = df[col_perdida].sum()
        total_ganancias = df[col_ganancia].sum()
        resultado_financiero = total_ganancias - total_perdidas
        
        # 3. Agregados (Gastos Rechazados)
        palabras_agregados = ['MULTA', 'INTERES', 'SANCION', 'RETIRO', 'GASTO PERSONAL']
        filtro = df.iloc[:, 1].astype(str).str.upper().str.contains('|'.join(palabras_agregados), na=False)
        
        # Sumamos los montos de la columna de PÉRDIDAS para esas filas
        monto_agregados = df[filtro][col_perdida].sum()
        
        return {
            "resultado_contable": resultado_financiero,
            "total_agregados": monto_agregados,
            "rli_estimada": resultado_financiero + monto_agregados
        }
    except Exception as e:
        return f"Error técnico: {str(e)}"
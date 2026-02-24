import pandas as pd
import re

# Tildes para normalización consistente con nombres de columnas
_REPLAZOS_TILDE = [("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U")]


def normalizar_nombre(col):
    s = str(col).strip().upper()
    for viejo, nuevo in _REPLAZOS_TILDE:
        s = s.replace(viejo, nuevo)
    return s


def limpiar_monto(valor):
    if pd.isna(valor):
        return 0
    valor = str(valor)
    valor = re.sub(r"[^\d-]", "", valor)
    return int(valor) if valor != "" else 0


def _nombre_columna_codigo(columnas):
    """Devuelve el nombre real de la columna que normaliza a CODIGO, o None."""
    for c in columnas:
        if normalizar_nombre(c) == "CODIGO":
            return c
    return None


def procesar_balance_8_columnas(archivo):
    """
    Lee y normaliza un balance de 8 columnas desde Excel.
    Retorna un DataFrame limpio o un str con mensaje de error.
    """
    if archivo is None:
        return "Error: No se proporcionó archivo."

    try:
        df = pd.read_excel(archivo)
    except Exception as e:
        return f"Error al leer Excel: {type(e).__name__} — {str(e)}"

    if df.empty:
        return "Error: El archivo está vacío o no tiene filas."

    # Normalizar nombres de columnas
    df.columns = [normalizar_nombre(c) for c in df.columns]

    if "CUENTA" not in df.columns:
        return "Error: No se encontró columna 'CUENTA'. Verifique el formato del balance."

    # Filtrar filas de totales/resumen (se recalculará Utilidad/Pérdida del Ejercicio)
    palabras_filtro = ["TOTAL", "UTILIDAD DEL EJERCICIO", "PERDIDA DEL EJERCICIO", "RESULTADO"]

    def _sin_tilde(s):
        s = str(s).strip().upper()
        for v, n in _REPLAZOS_TILDE:
            s = s.replace(v, n)
        return s

    mask = df["CUENTA"].apply(lambda x: not any(p in _sin_tilde(x) for p in palabras_filtro))
    df = df[mask]

    if df.empty:
        return "Error: No quedaron filas de detalle después del filtro (solo totales)."

    # Limpiar columnas monetarias
    columnas_dinero = [
        "DEUDOR", "ACREEDOR", "ACTIVO", "PASIVO", "PERDIDA", "GANANCIA",
        "DEBITOS", "CREDITOS", "DEBE", "HABER",
    ]
    for col in columnas_dinero:
        if col in df.columns:
            df[col] = df[col].apply(limpiar_monto)

    # Calcular DEUDOR y ACREEDOR desde movimientos cuando existan (balance correcto 8 columnas)
    if "DEBITOS" in df.columns and "CREDITOS" in df.columns:
        de = df["DEBITOS"].astype(int)
        cr = df["CREDITOS"].astype(int)
        df["DEUDOR"] = (de - cr).clip(lower=0)
        df["ACREEDOR"] = (cr - de).clip(lower=0)
    elif "DEBE" in df.columns and "HABER" in df.columns:
        de = df["DEBE"].astype(int)
        ha = df["HABER"].astype(int)
        df["DEUDOR"] = (de - ha).clip(lower=0)
        df["ACREEDOR"] = (ha - de).clip(lower=0)
    # Si no hay columnas de movimiento, DEUDOR/ACREEDOR quedan como vienen del Excel (ya limpiados)

    return df

def detectar_gastos_rechazados(df):
    patron = 'MULTA|INTERESES MORATORIOS'
    if 'CUENTA' in df.columns:
        return df[df['CUENTA'].astype(str).str.upper().str.contains(patron, na=False)]
    return pd.DataFrame()

def validar_debe_haber_cuadra(df):
    """
    Valida que sum(DEBE) == sum(HABER) (balance de comprobación).
    Usa columnas DEBE/HABER o DEBITOS/CREDITOS. Retorna (cuadra, suma_debe, suma_haber).
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return True, 0, 0
    if "DEBE" in df.columns and "HABER" in df.columns:
        s_debe = int(df["DEBE"].sum())
        s_haber = int(df["HABER"].sum())
        return s_debe == s_haber, s_debe, s_haber
    if "DEBITOS" in df.columns and "CREDITOS" in df.columns:
        s_debe = int(df["DEBITOS"].sum())
        s_haber = int(df["CREDITOS"].sum())
        return s_debe == s_haber, s_debe, s_haber
    return True, 0, 0


def balance_8_columnas_para_display(df):
    """
    Clasifica según código (saldo ya en DEUDOR/ACREEDOR desde debe-haber):
      saldo = debe - haber; si saldo > 0: deudor=saldo, acreedor=0; sino: deudor=0, acreedor=abs(saldo)
      1xx → activo = deudor
      2xx → pasivo = acreedor
      3xx → pasivo = acreedor (patrimonio)
      4, 5 → perdida = deudor
      6, 7, 8 → ganancia = acreedor
    No modifica DEUDOR/ACREEDOR ni las filas Utilidad/Pérdida del Ejercicio.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    col_cod = _nombre_columna_codigo(df.columns)
    if not col_cod:
        return df
    if "CUENTA" not in df.columns or "DEUDOR" not in df.columns or "ACREEDOR" not in df.columns:
        return df
    df = df.copy()
    for c in ["ACTIVO", "PASIVO", "PERDIDA", "GANANCIA"]:
        if c not in df.columns:
            df[c] = 0

    for i in df.index:
        cuenta_val = str(df.at[i, "CUENTA"]).strip().lower()
        if cuenta_val in ("utilidad del ejercicio", "perdida del ejercicio"):
            continue
        cod = df.at[i, col_cod]
        try:
            primera = str(int(float(cod)))[0] if pd.notna(cod) and str(cod).strip() else ""
        except (ValueError, TypeError):
            primera = ""

        deudor = int(df.at[i, "DEUDOR"]) if pd.notna(df.at[i, "DEUDOR"]) else 0
        acreedor = int(df.at[i, "ACREEDOR"]) if pd.notna(df.at[i, "ACREEDOR"]) else 0

        # Solo clasificar ACTIVO, PASIVO, PERDIDA, GANANCIA; DEUDOR/ACREEDOR se mantienen
        df.at[i, "ACTIVO"] = 0
        df.at[i, "PASIVO"] = 0
        df.at[i, "PERDIDA"] = 0
        df.at[i, "GANANCIA"] = 0

        if primera == "1":
            df.at[i, "ACTIVO"] = deudor
        elif primera == "2":
            df.at[i, "PASIVO"] = acreedor
        elif primera == "3":
            df.at[i, "PASIVO"] = acreedor
        elif primera in ("4", "5"):
            df.at[i, "PERDIDA"] = deudor
        elif primera in ("6", "7", "8"):
            df.at[i, "GANANCIA"] = acreedor

    return df


def validar_activo_igual_pasivo(df):
    """
    Comprueba que Activo = Pasivo + Patrimonio (ecuación contable).
    En balance 8 columnas: suma(ACTIVO) debe igualar suma(PASIVO).
    Retorna (suma_activo, suma_pasivo, cuadra).
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return 0, 0, True
    suma_activo = int(df["ACTIVO"].sum()) if "ACTIVO" in df.columns else 0
    suma_pasivo = int(df["PASIVO"].sum()) if "PASIVO" in df.columns else 0
    cuadra = suma_activo == suma_pasivo
    return suma_activo, suma_pasivo, cuadra


def validar_y_calcular_resultado(df):
    """
    Calcula UTILIDAD DEL EJERCICIO = SUM(GANANCIA) - SUM(PERDIDA) (lógica contable chilena).
    Inserta la fila del resultado y retorna (DataFrame actualizado, monto_utilidad).
    Columnas faltantes se tratan como 0. No usa DEUDOR/ACREEDOR para el cálculo.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df, 0

    columnas = df.columns
    sum_ganancia = df["GANANCIA"].sum() if "GANANCIA" in columnas else 0
    sum_perdida = df["PERDIDA"].sum() if "PERDIDA" in columnas else 0
    utilidad = float(sum_ganancia - sum_perdida)

    nueva_fila = {col: 0 for col in df.columns}
    col_cod = _nombre_columna_codigo(columnas)

    if utilidad > 0:
        nueva_fila["CUENTA"] = "Utilidad del Ejercicio"
        nueva_fila["ACREEDOR"] = int(round(utilidad))
        nueva_fila["GANANCIA"] = 0
        nueva_fila["PERDIDA"] = 0
        if "PASIVO" in columnas:
            nueva_fila["PASIVO"] = int(round(utilidad))
    else:
        nueva_fila["CUENTA"] = "Pérdida del Ejercicio"
        nueva_fila["DEUDOR"] = int(round(abs(utilidad)))
        nueva_fila["PERDIDA"] = int(round(abs(utilidad)))
        nueva_fila["GANANCIA"] = 0
        if "ACTIVO" in columnas:
            nueva_fila["ACTIVO"] = int(round(abs(utilidad)))

    if col_cod:
        nueva_fila[col_cod] = 0

    df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
    return df, utilidad

"""
Módulo contable DaddyBalance: lectura, clasificación y validación de balances 8 columnas.

Requisitos mínimos del Excel (Sprint 5 - documentación):
- Obligatorio: una columna de cuenta (Cuenta, Nombre o equivalente).
- Obligatorio: un par de movimientos o saldos:
  - Débitos y Créditos, o
  - Debe y Haber, o
  - Deudor y Acreedor.
- Opcional: Código (recomendado para clasificación por plan chileno).
Si faltan cuenta o movimientos/saldos, procesar_balance_8_columnas devuelve mensaje de error.
"""
import pandas as pd
import re

# Tildes para normalización consistente con nombres de columnas
_REPLAZOS_TILDE = [("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U")]


# Mapa: nombre canónico -> conjuntos de nombres normalizados (entrada flexible Sprint 1)
_ALIASES_COLUMNAS = {
    "CODIGO": {"CODIGO", "COD", "CODIGO DE CUENTA", "NUMERO", "NRO", "NUMERO DE CUENTA", "CODIGO CUENTA"},
    "CUENTA": {"CUENTA", "NOMBRE", "NOMBRE DE CUENTA", "NOMBRE CUENTA", "DENOMINACION"},
    "DEBE": {"DEBE", "DEBITO"},
    "HABER": {"HABER", "CREDITO"},
    "DEBITOS": {"DEBITOS"},
    "CREDITOS": {"CREDITOS"},
    "DEUDOR": {"DEUDOR", "SALDO DEUDOR"},
    "ACREEDOR": {"ACREEDOR", "SALDO ACREEDOR"},
    "ACTIVO": {"ACTIVO"},
    "PASIVO": {"PASIVO"},
    "PERDIDA": {"PERDIDA", "PERDIDAS"},
    "GANANCIA": {"GANANCIA", "GANANCIAS"},
}


def normalizar_nombre(col):
    s = str(col).strip().upper()
    for viejo, nuevo in _REPLAZOS_TILDE:
        s = s.replace(viejo, nuevo)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _aplicar_alias_columnas(df):
    """
    Renombra columnas según alias (Sprint 1: entrada flexible).
    Cada columna normalizada se mapea al primer canónico que coincida.
    """
    if df is None or df.empty:
        return df
    renombrar = {}
    usados = set()
    for col in df.columns:
        norm = normalizar_nombre(col)
        for canonico, aliases in _ALIASES_COLUMNAS.items():
            if norm in aliases and canonico not in usados:
                renombrar[col] = canonico
                usados.add(canonico)
                break
        else:
            renombrar[col] = col
    return df.rename(columns=renombrar)


def _tiene_movimientos_o_saldos(df):
    """True si hay al menos DEBE+HABER, o DEBITOS+CREDITOS, o DEUDOR+ACREEDOR."""
    c = df.columns
    return (
        ("DEBE" in c and "HABER" in c)
        or ("DEBITOS" in c and "CREDITOS" in c)
        or ("DEUDOR" in c and "ACREEDOR" in c)
    )


def _mensaje_falta_columnas(df):
    """Mensaje claro cuando falta el mínimo obligatorio (Sprint 1)."""
    if "CUENTA" not in df.columns:
        return "Error: No se encontró columna de cuenta. Debe existir una columna 'Cuenta' o 'Nombre' (o equivalente)."
    if not _tiene_movimientos_o_saldos(df):
        return (
            "Error: No se encontraron columnas de movimientos ni saldos. "
            "Debe haber Débitos/Créditos, o Debe/Haber, o Deudor/Acreedor (o equivalentes)."
        )
    return None


def limpiar_monto(valor):
    if pd.isna(valor):
        return 0
    # Si ya es numérico (Excel suele traer float), convertir a int sin tocar string (evitar que 5000000.0 -> "5000000.0" -> 50000000)
    if isinstance(valor, (int, float)):
        return int(round(float(valor)))
    valor = str(valor).strip()
    valor = re.sub(r"[^\d\-.,]", "", valor)
    if not valor or valor == "-":
        return 0
    neg = valor.startswith("-")
    if neg:
        valor = valor[1:]
    if "." in valor and "," in valor:
        if valor.rfind(",") > valor.rfind("."):
            valor = valor.replace(".", "").replace(",", ".")
        else:
            valor = valor.replace(",", "")
    elif "," in valor:
        partes = valor.split(",")
        if len(partes) == 2 and len(partes[1]) <= 2:
            valor = partes[0] + "." + partes[1]
        else:
            valor = valor.replace(",", "")
    else:
        valor = valor.replace(".", "")
    try:
        n = int(round(float(valor)))
        return -n if neg else n
    except ValueError:
        return 0


def _nombre_columna_codigo(columnas):
    """Devuelve el nombre real de la columna que normaliza a CODIGO, o None."""
    for c in columnas:
        if normalizar_nombre(c) == "CODIGO":
            return c
    return None


def procesar_balance_8_columnas(archivo):
    """
    Lee y normaliza un balance de 8 columnas desde Excel.
    Mínimo: columna Cuenta (o Nombre) + Débitos/Créditos, o Debe/Haber, o Deudor/Acreedor.
    Si el archivo tiene varias hojas, usa la primera que tenga cuenta y movimientos/saldos (detección automática).
    Si hay varias filas por cuenta (movimientos), agrupa y suma (Sprint 3).
    Retorna un DataFrame limpio o un str con mensaje de error.
    """
    if archivo is None:
        return "Error: No se proporcionó archivo."

    try:
        xl = pd.ExcelFile(archivo)
    except Exception as e:
        return f"Error al leer Excel: {type(e).__name__} — {str(e)}"

    if not xl.sheet_names:
        return "Error: El archivo no contiene hojas."

    df = None
    ultimo_error = None

    for sheet_name in xl.sheet_names:
        try:
            hoja = xl.parse(sheet_name=sheet_name)
        except Exception:
            continue
        if hoja.empty:
            continue
        # Aplicar alias y normalizar igual que más abajo
        hoja = _aplicar_alias_columnas(hoja)
        hoja.columns = [normalizar_nombre(c) for c in hoja.columns]
        hoja = hoja.loc[:, ~hoja.columns.duplicated(keep="first")]
        msg = _mensaje_falta_columnas(hoja)
        if msg is None:
            df = hoja
            break
        ultimo_error = msg

    if df is None:
        return (
            ultimo_error
            if ultimo_error
            else "Error: En ninguna hoja del archivo se encontraron los datos mínimos requeridos "
            "(columna de cuenta y Débitos/Créditos, o Debe/Haber, o Deudor/Acreedor)."
        )

    if df.empty:
        return "Error: El archivo está vacío o no tiene filas."

    # Eliminar columnas duplicadas (mismo nombre): quedarse con la primera (ya hecho en el bucle)
    df = df.loc[:, ~df.columns.duplicated(keep="first")]

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

    # Sprint 3: si hay varias filas por misma cuenta (movimientos), agrupar y sumar movimientos
    group_cols = ["CODIGO", "CUENTA"] if "CODIGO" in df.columns else ["CUENTA"]
    if "CODIGO" in df.columns:
        df["CODIGO"] = df["CODIGO"].fillna(0)
    if df.duplicated(subset=group_cols).any():
        cols_sum = [
            c for c in columnas_dinero
            if c in df.columns
        ]
        if cols_sum:
            df = df.groupby(group_cols, dropna=False)[cols_sum].sum().reset_index()

    # Calcular DEUDOR y ACREEDOR desde movimientos cuando existan (balance correcto 8 columnas)
    if "DEBITOS" in df.columns and "CREDITOS" in df.columns:
        de = df["DEBITOS"].astype(int)
        cr = df["CREDITOS"].astype(int)
        if "DEUDOR" not in df.columns:
            df["DEUDOR"] = (de - cr).clip(lower=0)
        if "ACREEDOR" not in df.columns:
            df["ACREEDOR"] = (cr - de).clip(lower=0)
    elif "DEBE" in df.columns and "HABER" in df.columns:
        de = df["DEBE"].astype(int)
        ha = df["HABER"].astype(int)
        if "DEUDOR" not in df.columns:
            df["DEUDOR"] = (de - ha).clip(lower=0)
        if "ACREEDOR" not in df.columns:
            df["ACREEDOR"] = (ha - de).clip(lower=0)
    # Si no hay columnas de movimiento, DEUDOR/ACREEDOR quedan como vienen del Excel (ya limpiados)

    return df


def combinar_balances(lista_df):
    """
    Combina varios balances ya procesados en uno solo (Sprint 1: carga múltiple).
    Agrupa por cuenta (CODIGO + CUENTA, o solo CUENTA) y suma columnas numéricas.
    Retorna un DataFrame o str con mensaje de error.
    """
    if not lista_df:
        return "Error: No hay datos para combinar."
    lista_df = [df for df in lista_df if isinstance(df, pd.DataFrame) and not df.empty]
    if not lista_df:
        return "Error: Ningún archivo válido para combinar."

    combined = pd.concat(lista_df, ignore_index=True)

    columnas_dinero = [
        "DEUDOR", "ACREEDOR", "ACTIVO", "PASIVO", "PERDIDA", "GANANCIA",
        "DEBITOS", "CREDITOS", "DEBE", "HABER",
    ]
    cols_num = [c for c in columnas_dinero if c in combined.columns]
    for c in cols_num:
        combined[c] = pd.to_numeric(combined[c], errors="coerce").fillna(0).astype(int)

    if "CODIGO" in combined.columns:
        group_cols = ["CODIGO", "CUENTA"]
        combined["CODIGO"] = combined["CODIGO"].fillna(0)
    else:
        group_cols = ["CUENTA"]

    combined = combined.groupby(group_cols, dropna=False)[cols_num].sum().reset_index()
    return combined


from modulos.config_renta import get_patrones_gastos_rechazados, regex_gastos_rechazados


def detectar_gastos_rechazados(df, patrones=None):
    """
    Filtra las filas del balance cuya cuenta coincide con los patrones de gastos rechazados.
    patrones: lista de strings (ej. ["MULTA", "INTERESES MORATORIOS"]); si es None, se usa
    la configuración de .streamlit/secrets.toml (GASTOS_RECHAZADOS) o el valor por defecto.
    """
    if "CUENTA" not in df.columns:
        return pd.DataFrame()
    patron_regex = regex_gastos_rechazados(patrones)
    if not patron_regex:
        return pd.DataFrame()
    return df[df["CUENTA"].astype(str).str.upper().str.contains(patron_regex, na=False)]

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
    Clasifica según plan de cuentas chileno estándar (Sprint 2):
      1 → Activo (deudor)
      2 → Pasivo (acreedor)
      3 → Patrimonio (acreedor, en columna Pasivo para cuadratura)
      4 → Ingresos → Ganancia (acreedor)
      5 → Costos → Pérdida (deudor)
      6 → Gastos → Pérdida (deudor)
      7 → Otros resultados → Ganancia (acreedor) por defecto
      8 → Cuentas de orden → no afecta resultado (no suma a Pérdida ni Ganancia)
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
        elif primera == "4":
            df.at[i, "GANANCIA"] = acreedor
        elif primera in ("5", "6"):
            df.at[i, "PERDIDA"] = deudor
        elif primera == "7":
            df.at[i, "GANANCIA"] = acreedor
        # 8 = cuentas de orden: no afecta resultado (queda 0 en PERDIDA y GANANCIA)

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

    # Hoja de trabajo / Balance 8 columnas:
    # - La fila de "Utilidad/Pérdida del Ejercicio" funciona como cierre:
    #   - Cuadra Estado de Resultados (Pérdida vs Ganancia)
    #   - Traspasa el resultado al Estado Patrimonial (Activo/Pasivo/Patrimonio)
    # - No representa un saldo (DEUDOR/ACREEDOR) propio, por eso quedan en 0.
    if utilidad > 0:
        # Utilidad: se registra en PÉRDIDA (deudor) para cuadrar ER y en PASIVO (acreedor/patrimonio) para cuadrar EP.
        nueva_fila["CUENTA"] = "Utilidad del Ejercicio"
        if "PERDIDA" in columnas:
            nueva_fila["PERDIDA"] = int(round(utilidad))
        if "PASIVO" in columnas:
            nueva_fila["PASIVO"] = int(round(utilidad))
    elif utilidad < 0:
        # Pérdida: se registra en GANANCIA (acreedor) para cuadrar ER y en ACTIVO (deudor) para cuadrar EP.
        perdida = int(round(abs(utilidad)))
        nueva_fila["CUENTA"] = "Pérdida del Ejercicio"
        if "GANANCIA" in columnas:
            nueva_fila["GANANCIA"] = perdida
        if "ACTIVO" in columnas:
            nueva_fila["ACTIVO"] = perdida
    else:
        # Resultado cero: dejar fila informativa sin impactos.
        nueva_fila["CUENTA"] = "Utilidad del Ejercicio"

    if col_cod:
        nueva_fila[col_cod] = 0

    df = pd.concat([df, pd.DataFrame([nueva_fila])], ignore_index=True)
    return df, utilidad

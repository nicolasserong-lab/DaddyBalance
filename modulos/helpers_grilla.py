"""
Helpers para grilla de balance: constantes, formato numérico, preparación de DF y mensajes de validación.
Centraliza lógica duplicada entre Cargar Balance y Análisis de Renta.
"""
__all__ = [
    "preparar_df_para_grilla", "agregar_filas_resumen_balance", "df_grilla_para_display",
    "fmt_entero", "altura_grilla", "mostrar_validacion_debe_haber", "mostrar_validacion_activo_pasivo",
    "render_grilla_agrupada",
]
import pandas as pd
import streamlit as st

# Columnas internas (sin tildes) en orden estándar
COLUMNAS_GRILLA_ORDEN = [
    "CODIGO", "CUENTA", "DEBE", "HABER", "DEUDOR", "ACREEDOR",
    "ACTIVO", "PASIVO", "PERDIDA", "GANANCIA",
]

# Nombres para mostrar en la grilla (encabezados centrados)
NOMBRES_GRILLA_DISPLAY = {
    "CODIGO": "Código", "CUENTA": "Cuenta", "DEBE": "Debe", "HABER": "Haber",
    "DEUDOR": "Deudor", "ACREEDOR": "Acreedor", "ACTIVO": "Activo", "PASIVO": "Pasivo",
    "PERDIDA": "Pérdida", "GANANCIA": "Ganancia",
}

ESTILO_ENCABEZADO_CENTRADO = [{"selector": "th", "props": [("text-align", "center")]}]


def fmt_miles(val):
    """Formatea valor para celda (miles con punto)."""
    if pd.isna(val):
        return ""
    try:
        return f"{int(float(val)):,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return str(val)


def fmt_entero(n):
    """Formatea entero para mensajes (ej. $ 1.234.567)."""
    return f"{int(n):,.0f}".replace(",", ".")


def altura_grilla(n_filas, alto_cabecera=36, alto_por_fila=26, min_altura=64, max_altura=420):
    """Calcula altura del dataframe para st.dataframe."""
    h = alto_cabecera + alto_por_fila * n_filas + 2
    return max(min_altura, min(h, max_altura))


def asegurar_debe_haber(df):
    """Añade DEBE/HABER desde DEBITOS/CREDITOS si no existen. Modifica copia."""
    df = df.copy()
    if "DEBE" not in df.columns:
        df["DEBE"] = df["DEBITOS"] if "DEBITOS" in df.columns else 0
    if "HABER" not in df.columns:
        df["HABER"] = df["CREDITOS"] if "CREDITOS" in df.columns else 0
    return df


def preparar_df_para_grilla(df):
    """Devuelve DF solo con columnas de grilla en orden (con DEBE/HABER asegurados)."""
    df = asegurar_debe_haber(df)
    cols = [c for c in COLUMNAS_GRILLA_ORDEN if c in df.columns]
    return df[cols].copy()


def agregar_filas_resumen_balance(df_grilla):
    """
    Inserta filas SUBTOTALES (antes de Utilidad) y TOTALES (después de Utilidad).
    Estructura final: [detalle] + [SUBTOTALES] + [Utilidad/Pérdida del Ejercicio] + [TOTALES].
    """
    if df_grilla.empty:
        return df_grilla.copy()

    cuenta_col = "CUENTA" if "CUENTA" in df_grilla.columns else None
    if not cuenta_col:
        return df_grilla.copy()

    # Identificar fila de resultado (última)
    mask_resultado = df_grilla[cuenta_col].astype(str).str.contains(
        "Utilidad del Ejercicio|Pérdida del Ejercicio", case=False, na=False
    )
    if not mask_resultado.any():
        return df_grilla.copy()

    df_detalle = df_grilla[~mask_resultado].copy()
    df_resultado = df_grilla[mask_resultado].copy()

    num_cols = [c for c in df_grilla.columns if c not in ("CODIGO", "CUENTA")]
    subtotales = df_detalle[num_cols].sum().astype(int)
    totales = subtotales + df_resultado[num_cols].iloc[0]

    # Importante (hoja de trabajo 8 columnas):
    # Los "SALDOS" (DEUDOR/ACREEDOR) deben cuadrar entre sí.
    # La utilidad/pérdida del ejercicio es un derivado del Estado de Resultados y se refleja
    # en Estado Patrimonial (Activo/Pasivo), no debe alterar el total de saldos.
    for c in ("DEUDOR", "ACREEDOR"):
        if c in totales.index and c in subtotales.index:
            totales[c] = int(subtotales[c])

    col_cod = "CODIGO" if "CODIGO" in df_grilla.columns else None
    fila_sub = {c: 0 for c in df_grilla.columns}
    fila_sub[cuenta_col] = "SUBTOTALES"
    if col_cod:
        fila_sub[col_cod] = ""
    for c in num_cols:
        fila_sub[c] = int(subtotales[c])

    fila_tot = {c: 0 for c in df_grilla.columns}
    fila_tot[cuenta_col] = "TOTALES"
    if col_cod:
        fila_tot[col_cod] = ""
    for c in num_cols:
        fila_tot[c] = int(totales[c])

    return pd.concat([
        df_detalle,
        pd.DataFrame([fila_sub]),
        df_resultado.reset_index(drop=True),
        pd.DataFrame([fila_tot]),
    ], ignore_index=True)


def df_grilla_para_display(df_grilla):
    """
    Renombra columnas a nombres display y devuelve (df_show, formato_numericas, col_codigo).
    formato_numericas es dict col -> fmt_miles para .style.format().
    """
    renombrar = {c: NOMBRES_GRILLA_DISPLAY[c] for c in df_grilla.columns if c in NOMBRES_GRILLA_DISPLAY}
    df_show = df_grilla.rename(columns=renombrar)
    col_codigo = "Código" if "Código" in df_show.columns else None
    numericas = df_show.select_dtypes(include=["number"]).columns
    cols_fmt = [c for c in numericas if c != col_codigo]
    formato = {c: fmt_miles for c in cols_fmt}
    return df_show, formato, col_codigo


def _filtrar_filas_resumen(df):
    """
    Remueve filas de resumen agregadas solo para display/exportación.
    Evita que validaciones (sumatorias) cuenten SUBTOTALES/TOTALES.
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        return df
    for col in ("CUENTA", "Cuenta"):
        if col in df.columns:
            s = df[col].astype(str).str.strip().str.upper()
            return df[~s.isin({"SUBTOTALES", "TOTALES"})]
    return df


def mostrar_validacion_debe_haber(df, validar_fn, prefijo="$ "):
    """Ejecuta validar_debe_haber_cuadra y muestra st.success o st.error."""
    df_val = _filtrar_filas_resumen(df)
    cuadra, suma_d, suma_h = validar_fn(df_val)
    if cuadra:
        st.success(f"✅ Balance de comprobación: Debe = Haber ({prefijo}{fmt_entero(suma_d)})")
    else:
        diff = abs(suma_d - suma_h)
        st.error(
            f"⚠️ Balance de comprobación no cuadra: Debe {prefijo}{fmt_entero(suma_d)} | "
            f"Haber {prefijo}{fmt_entero(suma_h)} | Diferencia {prefijo}{fmt_entero(diff)}"
        )


def mostrar_validacion_activo_pasivo(df, validar_fn, prefijo="$ ", titulo_ok="Ecuación contable", titulo_error="Ecuación contable no cuadra"):
    """Ejecuta validar_activo_igual_pasivo y muestra st.success o st.error."""
    df_val = _filtrar_filas_resumen(df)
    suma_a, suma_p, cuadra = validar_fn(df_val)
    if cuadra:
        st.success(f"✅ {titulo_ok}: Activo = Pasivo ({prefijo}{fmt_entero(suma_a)})")
    else:
        diff = abs(suma_a - suma_p)
        st.error(
            f"⚠️ {titulo_error}: Activo {prefijo}{fmt_entero(suma_a)} | "
            f"Pasivo {prefijo}{fmt_entero(suma_p)} | Diferencia {prefijo}{fmt_entero(diff)}"
        )


# Estructura de encabezados agrupados (inspirado en balance contable estándar)
# (grupo, subcolumnas) donde grupo es el encabezado padre y subcolumnas son las columnas del DF
ENCABEZADOS_AGRUPADOS = [
    ("N°", ["Código"]),
    ("Cuentas", ["Cuenta"]),
    ("Sumas", ["Debe", "Haber"]),
    ("Saldos", ["Deudor", "Acreedor"]),
    ("Estado Patrimonial", ["Activo", "Pasivo"]),
    ("Estado de Resultados", ["Pérdida", "Ganancia"]),
]


def _formatear_celda(val, col, formato, col_codigo):
    """Formatea valor de celda según columna."""
    if pd.isna(val):
        return ""
    if col in formato:
        return formato[col](val)
    if col in (col_codigo, "Código"):
        try:
            return str(int(float(val))) if isinstance(val, (int, float)) else str(val)
        except (ValueError, TypeError):
            return str(val)
    return fmt_miles(val)


def render_grilla_agrupada(df_show, formato, max_height_px=550, codigos_rechazo=None, col_codigo="Código"):
    """
    Renderiza la grilla como tabla HTML con encabezados agrupados en dos filas.
    Mantiene el diseño oscuro de la app. Centra todo el texto.
    codigos_rechazo: set de códigos a resaltar en rojo (Análisis Renta).
    """
    # Orden de columnas según ENCABEZADOS_AGRUPADOS
    col_order = []
    for _, subcols in ENCABEZADOS_AGRUPADOS:
        for c in subcols:
            if c in df_show.columns:
                col_order.append(c)
    if not col_order:
        col_order = list(df_show.columns)
    df_ordered = df_show[[c for c in col_order if c in df_show.columns]].copy()

    # Estilo: compacto, colores refinados
    header_style = (
        "background: linear-gradient(180deg, #1e3a5f 0%, #152a45 100%); color: #f8fafc; "
        "font-weight: 700; font-size: 0.75rem; letter-spacing: 0.2px; "
        "text-align: center; padding: 5px 8px; border: 1px solid #2d4a6f; "
        "vertical-align: middle;"
    )
    subheader_style = (
        "background: #243b53; color: #cbd5e1; font-weight: 600; font-size: 0.72rem; "
        "text-align: center; padding: 5px 8px; border: 1px solid #334155; "
        "vertical-align: middle;"
    )

    # Fila 1: grupos (rowspan para N° y Cuentas, colspan para el resto)
    th_grupos = []
    for grupo, subcols in ENCABEZADOS_AGRUPADOS:
        presentes = [c for c in subcols if c in df_ordered.columns]
        if not presentes:
            continue
        if len(presentes) == 1:
            th_grupos.append(f'<th rowspan="2" style="{header_style}">{grupo}</th>')
        else:
            th_grupos.append(f'<th colspan="{len(presentes)}" style="{header_style}">{grupo}</th>')

    # Fila 2: subencabezados (solo para grupos con >1 columna; N° y Cuentas ya ocupan con rowspan)
    th_sub = []
    for _, subcols in ENCABEZADOS_AGRUPADOS:
        if len(subcols) > 1:
            for c in subcols:
                if c in df_ordered.columns:
                    th_sub.append(f'<th style="{subheader_style}">{c}</th>')

    # Filas de datos (con estilos para SUBTOTALES, Utilidad, TOTALES) - filas ajustadas con más altura
    cuenta_col = "Cuenta" if "Cuenta" in df_ordered.columns else None
    filas_html = []
    for idx, row in df_ordered.iterrows():
        cuenta_val = str(row.get(cuenta_col, "")) if cuenta_col else ""
        if cuenta_val == "SUBTOTALES":
            row_style = "background: linear-gradient(180deg, #1e3a5f 0%, #152a45 100%); font-weight: 700; border-top: 2px solid rgba(34, 197, 94, 0.4);"
        elif cuenta_val == "TOTALES":
            row_style = "background: linear-gradient(180deg, #1e3a5f 0%, #152a45 100%); font-weight: 700;"
        elif "Utilidad del Ejercicio" in cuenta_val or "Pérdida del Ejercicio" in cuenta_val:
            row_style = "background: #243b53; font-weight: 600;"
        else:
            row_style = "background: #1e293b;" if idx % 2 == 0 else "background: #0f172a;"

        cells = []
        for col in df_ordered.columns:
            val = row[col]
            txt = _formatear_celda(val, col, formato, col_codigo)
            extra_style = ""
            if col == col_codigo and codigos_rechazo and txt and str(txt) in codigos_rechazo:
                extra_style = "background-color: rgba(239, 68, 68, 0.15); border-left: 4px solid #ef4444;"
            cell_style = f"{row_style} text-align: center; padding: 5px 8px; border: 1px solid #334155; color: #f1f5f9; font-size: 0.7rem; font-variant-numeric: tabular-nums; {extra_style}"
            cells.append(f'<td style="{cell_style}">{txt}</td>')
        filas_html.append("<tr>" + "".join(cells) + "</tr>")

    html = f"""
    <div class="grilla-balance-container" style="
        margin-bottom: 0.6rem;
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #334155;
        box-shadow: 0 2px 16px rgba(0,0,0,0.3);
        max-height: {max_height_px}px;
        overflow-y: auto;
        font-size: 90%;
    ">
    <table style="width: 100%; border-collapse: collapse; font-family: 'Plus Jakarta Sans', sans-serif;">
        <thead>
            <tr>{''.join(th_grupos)}</tr>
            <tr>{''.join(th_sub)}</tr>
        </thead>
        <tbody>{''.join(filas_html)}</tbody>
    </table>
    </div>
    """
    return html

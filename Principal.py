import io
import os
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import streamlit as st
import pandas as pd
import plotly.express as px

# Importamos las funciones de nuestros módulos
from modulos.calculos_renta import calcular_rli_basica 
from modulos.asistente_ia import generar_explicacion_renta 
from modulos.lector_contable import (
    procesar_balance_8_columnas,
    combinar_balances,
    detectar_gastos_rechazados,
    validar_y_calcular_resultado,
    balance_8_columnas_para_display,
    validar_debe_haber_cuadra,
    validar_activo_igual_pasivo,
    _nombre_columna_codigo,
)
from modulos.helpers_grilla import (
    preparar_df_para_grilla,
    agregar_filas_resumen_balance,
    df_grilla_para_display,
    fmt_entero,
    altura_grilla,
    mostrar_validacion_debe_haber,
    mostrar_validacion_activo_pasivo,
    render_grilla_agrupada,
)
from modulos.validaciones_carga import (
    validar_formato_archivo,
    validar_archivo_tiene_contenido,
    validar_estructura_8_columnas,
    get_solucion_validacion_basica,
    ESTRUCTURA_VALIDA,
)
from modulos import db

# Configuración de página
st.set_page_config(page_title="DaddyBalance v1.0", layout="wide", initial_sidebar_state="expanded")

# --- SISTEMA DE SEGURIDAD ---
# La contraseña se configura en .streamlit/secrets.toml como APP_PASSWORD (nunca en el código).
def check_password():
    password_esperada = st.secrets.get("APP_PASSWORD")
    if not password_esperada or not str(password_esperada).strip():
        st.title("🔒 Acceso Restringido")
        st.error(
            "No está configurada la contraseña de acceso. "
            "Agregue **APP_PASSWORD** en el archivo `.streamlit/secrets.toml`."
        )
        st.markdown("---")
        st.code("APP_PASSWORD = \"tu_contraseña_secreta\"", language="toml")
        return False

    def password_entered():
        p = st.session_state.get("password", "")
        if p == str(password_esperada).strip():
            st.session_state["password_correct"] = True
            if "password" in st.session_state:
                del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔒 Acceso Restringido")
        st.text_input("Ingrese la contraseña:", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔒 Acceso Restringido")
        st.text_input("Ingrese la contraseña:", type="password", on_change=password_entered, key="password")
        st.error("😕 Contraseña incorrecta")
        return False
    return True

if not check_password():
    st.stop()

# --- ESTILOS CSS NIVEL DIOS ---
# Tema oscuro forzado para que se vea igual en todos los notebooks/entornos
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

    /* Raíz y cuerpo: fondo oscuro siempre */
    html, body, .main .block-container, [data-testid="stAppViewContainer"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        background-color: #0b0e14 !important;
    }
    [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif !important;
    }
    .stApp {
        background-color: #0b0e14 !important;
    }

    .hero-title {
        font-size: 2.5rem !important;
        font-weight: 800 !important;
        background: linear-gradient(90deg, #ffffff 0%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem !important;
        letter-spacing: -1.5px;
    }
    
    .sub-hero {
        font-size: 1.2rem !important;
        color: #64748b !important;
        margin-bottom: 2.5rem !important;
        font-weight: 500;
    }

    .section-header-god {
        font-size: 1.6rem !important;
        font-weight: 700 !important;
        color: #f8fafc;
        margin-top: 2.5rem !important;
        margin-bottom: 1.2rem !important;
        display: flex;
        align-items: center;
        gap: 12px;
    }

    [data-testid="stMetric"] {
        background: rgba(30, 41, 59, 0.45) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 25px !important;
        border-radius: 24px !important;
        backdrop-filter: blur(12px) !important;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.3) !important;
    }
    
    [data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
    }
    
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2.4rem !important;
        font-weight: 800 !important;
    }

    .ai-box-premium {
        background: linear-gradient(145deg, #1e293b, #0f172a);
        padding: 35px;
        border-radius: 24px;
        border-left: 8px solid #10b981;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        color: #e2e8f0;
        line-height: 1.6;
    }

    [data-testid="stSidebar"] {
        background-color: #0f172a !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }

    /* Combo Panel de Control: fondo oscuro y texto claro en todos los entornos */
    [data-testid="stSidebar"] [data-testid="stSelectbox"] > div,
    [data-testid="stSidebar"] .stSelectbox > div > div,
    div[data-testid="stSelectbox"] div {
        background-color: #1e293b !important;
        color: #f8fafc !important;
    }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] label,
    [data-testid="stSidebar"] .stSelectbox label {
        color: #94a3b8 !important;
    }

    /* Área de carga de archivos (Cargar Balance / Análisis): fondo oscuro */
    section[data-testid="stFileUploader"] {
        background-color: #1e293b !important;
        border-radius: 12px !important;
    }
    section[data-testid="stFileUploader"] > div,
    [data-testid="stFileUploader"] section {
        background-color: #1e293b !important;
        border-color: rgba(255,255,255,0.1) !important;
    }
    [data-testid="stFileUploader"] label {
        color: #e2e8f0 !important;
    }

    .stDataFrame {
        border-radius: 20px !important;
        overflow: hidden !important;
        position: relative !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2) !important;
    }
    div[data-testid="stDataFrame"] {
        padding-bottom: 0 !important;
        overflow: hidden !important;
        position: relative !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 12px !important;
    }
    div[data-testid="stDataFrame"] > div {
        overflow: hidden !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    div[data-testid="stDataFrame"] th, div[data-testid="stDataFrame"] thead th {
        text-align: center !important;
    }
    /* Borde inferior y derecho de la tabla: última fila y última celda */
    div[data-testid="stDataFrame"] tbody tr:last-child td {
        border-bottom: 1px solid rgba(255, 255, 255, 0.15) !important;
    }
    div[data-testid="stDataFrame"] td:last-child,
    div[data-testid="stDataFrame"] th:last-child {
        border-right: 1px solid rgba(255, 255, 255, 0.15) !important;
    }
    /* Bloque Análisis Renta: contenedor y columnas alineadas */
    div[data-testid="stVerticalBlock"]:has(.stSelectbox):has(.stFileUploader) { gap: 0.5rem; }
    div[data-testid="stVerticalBlock"]:has(.stSelectbox):has(.stFileUploader) [data-testid="column"] {
        min-height: 88px; display: flex; flex-direction: column;
    }
    div[data-testid="stVerticalBlock"]:has(.stSelectbox):has(.stFileUploader) .stSelectbox label,
    div[data-testid="stVerticalBlock"]:has(.stSelectbox):has(.stFileUploader) .stFileUploader label {
        font-size: 0.9rem !important; font-weight: 600 !important; color: #94a3b8 !important; margin-bottom: 0.35rem !important;
    }
    div[data-testid="stVerticalBlock"]:has(.stSelectbox):has(.stFileUploader) .stFileUploader [data-testid="stFileUploader"] section {
        padding: 0.85rem 1.1rem !important; min-height: 68px !important; border-radius: 12px;
    }
    div[data-testid="stDataFrame"] td:last-child,
    div[data-testid="stDataFrame"] th:last-child {
        border-right: 1px solid rgba(255, 255, 255, 0.15) !important;
    }
    /* Franja bajo la última fila: mismo color que el borde para cerrar visualmente la grilla */
    div[data-testid="stDataFrame"]::after {
        content: "";
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: rgba(255, 255, 255, 0.12);
        pointer-events: none;
    }
    
    /* Grilla balance: scrollbar y espaciado para evitar traslape con mensajes */
    .grilla-balance-container {
        scrollbar-width: thin;
        scrollbar-color: rgba(148,163,184,0.4) transparent;
    }
    .grilla-balance-container::-webkit-scrollbar { width: 8px; height: 8px; }
    .grilla-balance-container::-webkit-scrollbar-track { background: rgba(15,23,42,0.5); }
    .grilla-balance-container::-webkit-scrollbar-thumb { background: rgba(148,163,184,0.4); border-radius: 4px; }

    /* Centrar icono DaddyBalance */
    .sidebar-logo {
        display: flex;
        justify-content: center;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGACIÓN ---
with st.sidebar:
    # Contenedor para el logo con fallback y estilo
    st.markdown(
        """
        <div style="display: flex; justify-content: center; padding: 20px 0;">
            <div style="background-color: #1e293b; padding: 20px; border-radius: 50%; border: 2px solid #3b82f6; box-shadow: 0 0 15px rgba(59, 130, 246, 0.5);">
                <img src="https://cdn-icons-png.flaticon.com/512/2652/2652234.png" width="60" style="filter: brightness(0) invert(1);">
            </div>
        </div>
        <h2 style="text-align: center; color: white; font-size: 1.5rem; margin-top: -10px;">DaddyBalance</h2>
        """, 
        unsafe_allow_html=True
    )
    
    st.markdown("---")
    st.markdown("### Panel de Control")
    opcion = st.selectbox("Seleccione Función", ["Inicio", "Cargar Balance", "Análisis de Renta", "Ver historial"], label_visibility="collapsed")
    st.markdown("---")
    st.info("💡 **D3**: Tasa 10% s/ RLI\n\n💡 **D8**: Atribuido a socios")

# --- SECCIÓN 1: INICIO ---
if opcion == "Inicio":
    st.markdown('<p class="hero-title">Dashboard Global</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-hero">Estado actual de su cartera contable y auditoría automatizada.</p>', unsafe_allow_html=True)

    # Sprint D: datos reales desde Supabase
    stats = db.obtener_estadisticas_inicio()
    actividades = db.obtener_ultimas_actividades(limite=10)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Cargas de Balance", str(stats.get("total_cargas", 0)), "Registros en historial")
    with col2:
        st.metric("Análisis de Renta", str(stats.get("total_analisis", 0)), "Cálculos RLI")
    with col3:
        ultima_rli = stats.get("ultima_rli")
        ultimo_imp = stats.get("ultimo_impuesto")
        if ultima_rli is not None or ultimo_imp is not None:
            st.metric(
                "Última RLI / Impuesto",
                f"$ {fmt_entero(ultima_rli or 0)}" if ultima_rli is not None else "—",
                f"Impuesto $ {fmt_entero(ultimo_imp or 0)}" if ultimo_imp is not None else "",
            )
        else:
            st.metric("Última RLI / Impuesto", "—", "Sin datos aún")

    st.markdown('<p class="section-header-god">🚀 Actividad Reciente</p>', unsafe_allow_html=True)
    with st.container(border=True):
        if not actividades:
            st.markdown("**Aún no hay actividad.** Usá *Cargar Balance* o *Análisis de Renta* para generar registros. Si ya configuraste Supabase, los verás aquí.")
        else:
            ZONA_CHILE = ZoneInfo("America/Santiago")
            for a in actividades:
                tipo = a.get("tipo") or ""
                fecha_raw = a.get("fecha")
                try:
                    if isinstance(fecha_raw, str) and "T" in fecha_raw:
                        d = datetime.fromisoformat(fecha_raw.replace("Z", "+00:00"))
                        if d.tzinfo is None:
                            d = d.replace(tzinfo=timezone.utc)
                        d_chile = d.astimezone(ZONA_CHILE)
                        fecha_str = d_chile.strftime("%d/%m/%Y %H:%M")
                    else:
                        fecha_str = str(fecha_raw)[:16] if fecha_raw else "—"
                except Exception:
                    fecha_str = str(fecha_raw)[:16] if fecha_raw else "—"
                desc = (a.get("descripcion") or "").strip() or "—"
                if tipo == "carga_balance":
                    icono = "📁"
                    extra = ""
                    if a.get("resultado_contable") is not None:
                        extra = f" · Utilidad $ {fmt_entero(a['resultado_contable'])}"
                    st.markdown(f"* **{icono} {fecha_str}** — {desc}{extra}")
                else:
                    icono = "🤖"
                    rli = a.get("rli")
                    imp = a.get("impuesto")
                    extra = ""
                    if rli is not None or imp is not None:
                        extra = f" · RLI $ {fmt_entero(rli or 0)} · Impuesto $ {fmt_entero(imp or 0)}"
                    st.markdown(f"* **{icono} {fecha_str}** — {desc}{extra}")

# --- SECCIÓN 2: CARGAR BALANCE ---
elif opcion == "Cargar Balance":
    st.markdown('<p class="hero-title">Carga de Datos</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-hero">Importación masiva de balances de 8 columnas. Puedes subir varios archivos; se combinarán en un solo balance.</p>', unsafe_allow_html=True)

    with st.container(border=True):
        archivos_subidos = st.file_uploader(
            "Arrastra uno o más archivos Excel aquí",
            type=["xlsx", "xls"],
            key="carga_balance",
            accept_multiple_files=True,
        )

    if archivos_subidos:
        # SPRINT 1: Validaciones básicas de archivo (formato + contenido). No se genera balance aún.
        error_validacion = None
        for archivo in archivos_subidos:
            ok_formato, msg_formato = validar_formato_archivo(archivo)
            if not ok_formato:
                error_validacion = msg_formato
                break
            ok_contenido, msg_contenido = validar_archivo_tiene_contenido(archivo)
            if not ok_contenido:
                error_validacion = msg_contenido
                break

        if error_validacion:
            st.error(error_validacion)
            solucion = get_solucion_validacion_basica(error_validacion)
            if solucion:
                with st.expander("¿Por qué aparece este mensaje y cómo solucionarlo?"):
                    st.markdown(solucion)
        else:
            st.success("✅ Validación básica correcta. Los archivos cumplen con los requisitos (formato Excel y contenido válido).")
            # Clasificación: solo mostrar "Estructura válida" cuando el archivo tiene Balance 8 columnas; si no, no desplegar mensaje.
            estructura_valida = True
            for archivo in archivos_subidos:
                if hasattr(archivo, "seek"):
                    archivo.seek(0)
                es_valida, _, _ = validar_estructura_8_columnas(archivo)
                if not es_valida:
                    estructura_valida = False
                    break
            if estructura_valida:
                st.info(f"📋 **Clasificación:** {ESTRUCTURA_VALIDA}")
            # Generar grilla balance 8 columnas (con o sin estructura 8 columnas): procesar, combinar y mostrar sin validaciones adicionales.
            lista_df = []
            error_proceso = None
            for archivo in archivos_subidos:
                if hasattr(archivo, "seek"):
                    archivo.seek(0)
                resultado = procesar_balance_8_columnas(archivo)
                if isinstance(resultado, str):
                    error_proceso = resultado
                    break
                lista_df.append(resultado)
            if error_proceso:
                st.error(error_proceso)
                with st.expander("¿Por qué aparece este mensaje y cómo solucionarlo?"):
                    st.markdown(
                        "**¿Por qué aparece este mensaje?** El archivo no pudo convertirse a un balance de 8 columnas. "
                        "Puede faltar la columna de cuenta (Cuenta/Nombre), las columnas de movimientos (Debe/Haber o Débitos/Créditos o Deudor/Acreedor), "
                        "o el archivo solo contiene filas de totales.\n\n"
                        "**Cómo solucionarlo:** Asegúrese de que el Excel tenga al menos una hoja con columnas de cuenta y de movimientos o saldos, "
                        "y filas de detalle (no solo totales o encabezados)."
                    )
            elif lista_df:
                combined = combinar_balances(lista_df)
                if isinstance(combined, str):
                    st.error(combined)
                    with st.expander("¿Por qué aparece este mensaje y cómo solucionarlo?"):
                        st.markdown(f"**Detalle:** {combined}")
                else:
                    df_display = balance_8_columnas_para_display(combined)
                    df_grilla, utilidad = validar_y_calcular_resultado(df_display.copy())
                    df_grilla = preparar_df_para_grilla(df_grilla)
                    df_grilla = agregar_filas_resumen_balance(df_grilla)
                    df_show, formato_final, col_codigo_show = df_grilla_para_display(df_grilla)
                    # Sprint C: registrar en Supabase para historial e Inicio
                    _rc = None
                    if utilidad is not None and utilidad == utilidad:
                        try:
                            _rc = int(round(utilidad))
                        except (TypeError, ValueError):
                            pass
                    db.guardar_carga_balance(
                        descripcion="Carga de balance",
                        resultado_contable=_rc,
                    )
                    st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
                    st.markdown("<h3 style='margin-bottom: 0;'>📊 Grilla de Balance</h3>", unsafe_allow_html=True)
                    html_grilla = render_grilla_agrupada(
                        df_show, formato_final,
                        max_height_px=int(altura_grilla(len(df_show))),
                        codigos_rechazo=set(),
                        col_codigo=col_codigo_show,
                    )
                    st.markdown(html_grilla, unsafe_allow_html=True)
                    buffer = io.BytesIO()
                    df_show.to_excel(buffer, index=False, engine="openpyxl")
                    buffer.seek(0)
                    col_dl, col_save = st.columns(2)
                    with col_dl:
                        st.download_button(
                            label="📥 Descargar Excel",
                            data=buffer.getvalue(),
                            file_name="balance_cargado.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_carga_balance",
                        )
                    with col_save:
                        nombre_guardar = st.text_input(
                            "Nombre del archivo para guardar",
                            placeholder="ej. 01 Balance Gral",
                            key="nombre_guardar_balance",
                        )
                        if st.button("💾 Guardar balance", key="btn_guardar_balance"):
                            if not (nombre_guardar or nombre_guardar.strip()):
                                st.warning("Ingrese un nombre para el archivo.")
                            else:
                                # Sanitizar: espacios -> _, quitar caracteres no válidos para nombre de archivo
                                nombre_base = re.sub(r"[\s]+", "_", nombre_guardar.strip())
                                nombre_base = re.sub(r'[\\/:*?"<>|]', "", nombre_base) or "balance"
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                nombre_archivo = f"{nombre_base}_{timestamp}.xlsx"
                                carpeta = os.path.join(os.path.dirname(__file__), "documentos", "balances_guardados")
                                os.makedirs(carpeta, exist_ok=True)
                                ruta_completa = os.path.join(carpeta, nombre_archivo)
                                df_show.to_excel(ruta_completa, index=False, engine="openpyxl")
                                st.success(f"✅ Balance guardado en: **{nombre_archivo}**")

# --- SECCIÓN 3: ANÁLISIS DE RENTA (DISEÑO REFINADO) ---
elif opcion == "Análisis de Renta":
    st.markdown('<p class="hero-title">Análisis de Renta Líquida Imponible</p>', unsafe_allow_html=True)

    with st.container(border=True):
        col_reg, col_file = st.columns([1, 2])
        with col_reg:
            regimen_sel = st.selectbox("Seleccione el Régimen Tributario:", 
                                      ["Propyme General (14 D3)", "Propyme Transparente (14 D8)"],
                                      key="regimen_renta")
        with col_file:
            archivos_renta = st.file_uploader(
                "Sube uno o más balances para el cálculo (se combinarán en uno)",
                type=["xlsx", "xls"],
                key="archivo_renta",
                accept_multiple_files=True,
            )
    
    if archivos_renta:
        # Validaciones básicas (formato + contenido) como en Cargar Balance
        error_validacion = None
        for archivo in archivos_renta:
            ok_formato, msg_formato = validar_formato_archivo(archivo)
            if not ok_formato:
                error_validacion = msg_formato
                break
            ok_contenido, msg_contenido = validar_archivo_tiene_contenido(archivo)
            if not ok_contenido:
                error_validacion = msg_contenido
                break

        if error_validacion:
            st.error(error_validacion)
            solucion = get_solucion_validacion_basica(error_validacion)
            if solucion:
                with st.expander("¿Por qué aparece este mensaje y cómo solucionarlo?"):
                    st.markdown(solucion)
        else:
            lista_df_renta = []
            error_proceso = None
            for archivo in archivos_renta:
                if hasattr(archivo, "seek"):
                    archivo.seek(0)
                resultado = procesar_balance_8_columnas(archivo)
                if isinstance(resultado, str):
                    error_proceso = resultado
                    break
                lista_df_renta.append(resultado)

            if error_proceso:
                st.error(error_proceso)
                with st.expander("¿Por qué aparece este mensaje y cómo solucionarlo?"):
                    st.markdown(
                        "**¿Por qué aparece este mensaje?** El archivo no pudo convertirse a un balance de 8 columnas. "
                        "Puede faltar la columna de cuenta (Cuenta/Nombre), las columnas de movimientos (Debe/Haber o Débitos/Créditos o Deudor/Acreedor), "
                        "o el archivo solo contiene filas de totales.\n\n"
                        "**Cómo solucionarlo:** Asegúrese de que el Excel tenga al menos una hoja con columnas de cuenta y de movimientos o saldos, "
                        "y filas de detalle (no solo totales o encabezados)."
                    )
            elif lista_df_renta:
                combined_renta = combinar_balances(lista_df_renta)
                if isinstance(combined_renta, str):
                    st.error(combined_renta)
                    with st.expander("¿Por qué aparece este mensaje y cómo solucionarlo?"):
                        st.markdown(f"**Detalle:** {combined_renta}")
                else:
                    df_renta = balance_8_columnas_para_display(combined_renta)
                    # Sprint 5: clasificar por plan chileno antes de RLI para que tarjetas y gráficos usen mismos datos
                    resultados = calcular_rli_basica(df_renta, regimen=regimen_sel)
                    detalle_gastos = detectar_gastos_rechazados(df_renta)

                    # Sprint C: registrar análisis de renta en Supabase
                    r = resultados
                    db.guardar_analisis_renta(
                        descripcion="Análisis de Renta",
                        resultado_contable=int(r["resultado_contable"]) if r.get("resultado_contable") is not None else None,
                        rli=int(r["rli_estimada"]) if r.get("rli_estimada") is not None else None,
                        impuesto=int(r["impuesto_pagar"]) if r.get("impuesto_pagar") is not None else None,
                        regimen=regimen_sel,
                    )

                    # --- 2. TARJETAS DE MÉTRICAS ---
                    st.markdown("---")
                    r = resultados
                    tasa_pct = int(r["tasa_aplicada"] * 100)
                    cards_html = f"""
            <style>
            .metric-cards-row {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }}
            .metric-card {{ flex: 1; min-width: 200px; min-height: 118px; padding: 16px 20px; border-radius: 16px;
                border: 1px solid rgba(255,255,255,0.1); background: rgba(30,41,59,0.45);
                display: flex; flex-direction: column; justify-content: center; }}
            .metric-card .label {{ color: #94a3b8; font-size: 0.85rem; font-weight: 600; margin-bottom: 4px; }}
            .metric-card .value {{ color: #fff; font-size: 1.6rem; font-weight: 800; margin: 0 0 4px 0; line-height: 1.2; }}
            .metric-card .detail {{ font-size: 0.8rem; margin-top: 2px; line-height: 1.2; }}
            </style>
            <div class="metric-cards-row">
                <div class="metric-card">
                    <div class="label">Utilidad Financiera</div>
                    <div class="value">$ {fmt_entero(r['resultado_contable'])}</div>
                    <div class="detail">&nbsp;</div>
                </div>
                <div class="metric-card">
                    <div class="label">(+) Agregados (Gastos)</div>
                    <div class="value">$ {fmt_entero(r['total_agregados'])}</div>
                    <div class="detail" style="color:#ef4444;">↑ Gasto Rechazado</div>
                </div>
                <div class="metric-card">
                    <div class="label">RLI Estimada</div>
                    <div class="value">$ {fmt_entero(r['rli_estimada'])}</div>
                    <div class="detail" style="color:#10b981;">↑ Base Imponible</div>
                </div>
                <div class="metric-card">
                    <div class="label">Impuesto IDPC</div>
                    <div class="value">$ {fmt_entero(r['impuesto_pagar'])}</div>
                    <div class="detail" style="color:#3b82f6;">↑ Tasa {tasa_pct}%</div>
                </div>
            </div>
            """
                    st.markdown(cards_html, unsafe_allow_html=True)

                    # --- 3. GRÁFICOS Y ANÁLISIS ---
                    col_chart1, col_chart2 = st.columns(2)
                    with col_chart1:
                        with st.container(border=True):
                            st.markdown("**Composición de la RLI**")
                            datos_torta = pd.DataFrame({
                                "Concepto": ["Utilidad", "Gastos Rechazados"],
                                "Monto": [max(0, resultados['resultado_contable']), resultados['total_agregados']]
                            })
                            fig = px.pie(datos_torta, values='Monto', names='Concepto', hole=0.6,
                                         color_discrete_sequence=['#10b981', '#ef4444'])
                            fig.update_layout(template="plotly_dark", height=300, margin=dict(t=20, b=20, l=0, r=0))
                            st.plotly_chart(fig, width="stretch")

                    with col_chart2:
                        with st.container(border=True):
                            st.markdown("**Relación RLI vs Impuesto**")
                            datos_bar = pd.DataFrame({
                                "Concepto": ["RLI", "Impuesto"],
                                "Valor": [resultados['rli_estimada'], resultados['impuesto_pagar']]
                            })
                            fig_bar = px.bar(datos_bar, x='Concepto', y='Valor', color='Concepto',
                                             color_discrete_map={'RLI': '#3b82f6', 'Impuesto': '#f59e0b'})
                            fig_bar.update_layout(template="plotly_dark", height=300, showlegend=False)
                            st.plotly_chart(fig_bar, width="stretch")

                    # --- 4. CONSULTOR IA ---
                    st.markdown("### 🤖 Consultor DaddyBalance")
                    explicacion = generar_explicacion_renta(resultados, detalle_gastos)
                    st.markdown(f"<div class='ai-box-premium'>{explicacion}</div>", unsafe_allow_html=True)

                    # --- 5. GRILLA DE AUDITORÍA ---
                    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
                    st.markdown("<h3 style='margin-bottom: 0;'>📊 Grilla de Auditoría</h3>", unsafe_allow_html=True)
                    mostrar_validacion_debe_haber(df_renta, validar_debe_haber_cuadra, prefijo="$ ")
                    df_grilla, _ = validar_y_calcular_resultado(df_renta.copy())
                    df_grilla = preparar_df_para_grilla(df_grilla)
                    df_grilla = agregar_filas_resumen_balance(df_grilla)
                    df_show, formato_final, col_codigo_show = df_grilla_para_display(df_grilla)

                    codigos_rechazo = set()
                    if detalle_gastos is not None and not detalle_gastos.empty:
                        col_codigo_dg = _nombre_columna_codigo(detalle_gastos.columns)
                        if col_codigo_dg:
                            codigos_rechazo = set(str(c) for c in detalle_gastos[col_codigo_dg].dropna())

                    html_grilla = render_grilla_agrupada(
                        df_show, formato_final,
                        max_height_px=int(altura_grilla(len(df_show))),
                        codigos_rechazo=codigos_rechazo,
                        col_codigo=col_codigo_show,
                    )
                    st.markdown(html_grilla, unsafe_allow_html=True)
                    st.markdown("<div style='margin-top: 0.5rem;'></div>", unsafe_allow_html=True)
                    mostrar_validacion_activo_pasivo(df_grilla, validar_activo_igual_pasivo, prefijo="$ ", titulo_error="Balance 8 columnas descuadrado")
                    # Botón de descarga Excel debajo de la grilla
                    buffer = io.BytesIO()
                    df_show.to_excel(buffer, index=False, engine="openpyxl")
                    buffer.seek(0)
                    st.download_button(
                        label="📥 Descargar Excel",
                        data=buffer,
                        file_name="grilla_auditoria.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                    # Nota: cómo se calcula todo (con datos reales de la grilla)
                    # Importante: df_grilla aquí incluye SUBTOTALES/TOTALES (solo display). Para cálculos reales, excluirlas.
                    # Además, la fila "Utilidad/Pérdida del Ejercicio" es un asiento de cierre (cuadra ER),
                    # por lo que para mostrar Ganancias - Pérdidas se debe excluir esa fila.
                    df_grilla_val = df_grilla
                    if "CUENTA" in df_grilla.columns:
                        _s = df_grilla["CUENTA"].astype(str).str.strip().str.upper()
                        df_grilla_val = df_grilla[~_s.isin({"SUBTOTALES", "TOTALES"})]

                    df_grilla_pre_cierre = df_grilla_val
                    if "CUENTA" in df_grilla_val.columns:
                        _t = df_grilla_val["CUENTA"].astype(str).str.strip().str.upper()
                        df_grilla_pre_cierre = df_grilla_val[~_t.str.contains("UTILIDAD DEL EJERCICIO|PERDIDA DEL EJERCICIO", na=False)]

                    total_debe_n = int(df_grilla_pre_cierre["DEBE"].sum()) if "DEBE" in df_grilla_pre_cierre.columns else 0
                    total_haber_n = int(df_grilla_pre_cierre["HABER"].sum()) if "HABER" in df_grilla_pre_cierre.columns else 0
                    total_ganancia_n = int(df_grilla_pre_cierre["GANANCIA"].sum()) if "GANANCIA" in df_grilla_pre_cierre.columns else 0
                    total_perdida_n = int(df_grilla_pre_cierre["PERDIDA"].sum()) if "PERDIDA" in df_grilla_pre_cierre.columns else 0
                    utilidad_n = total_ganancia_n - total_perdida_n
                    cuadra_debe_haber, _, _ = validar_debe_haber_cuadra(df_renta)
                    suma_activo, suma_pasivo, cuadra_balance = validar_activo_igual_pasivo(df_grilla_val)

                    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
                    nota_html = f"""
            <div style="
                background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 16px;
                padding: 24px 28px;
                margin-top: 16px;
                font-family: 'Plus Jakarta Sans', sans-serif;
                color: #e2e8f0;
            ">
                <div style="font-size: 1.1rem; font-weight: 700; color: #94a3b8; margin-bottom: 20px;">📊 Cómo se calcula el balance</div>
                <div style="display: grid; gap: 20px;">
                    <div style="background: rgba(30,41,59,0.6); border-radius: 12px; padding: 16px 20px; border-left: 4px solid #3b82f6;">
                        <div style="font-weight: 700; margin-bottom: 8px;">1️⃣ Validación de sumas</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 12px; align-items: baseline;">
                            <span>Total Debe <strong style="color: #fff;">{fmt_entero(total_debe_n)}</strong></span>
                            <span style="color: #64748b;">|</span>
                            <span>Total Haber <strong style="color: #fff;">{fmt_entero(total_haber_n)}</strong></span>
                            <span style="margin-left: 8px;">{'✔ Debe = Haber' if cuadra_debe_haber else '✘ No cuadra'}</span>
                        </div>
                    </div>
                    <div style="background: rgba(30,41,59,0.6); border-radius: 12px; padding: 16px 20px; border-left: 4px solid #10b981;">
                        <div style="font-weight: 700; margin-bottom: 8px;">2️⃣ Cálculo de utilidad</div>
                        <div style="color: #94a3b8; font-size: 0.95rem;">
                            Ganancias: <strong style="color: #10b981;">{fmt_entero(total_ganancia_n)}</strong> &nbsp;&nbsp;−&nbsp;&nbsp;
                            Pérdidas: <strong style="color: #f59e0b;">{fmt_entero(total_perdida_n)}</strong>
                            &nbsp;&nbsp;=&nbsp;&nbsp; Utilidad: <strong style="color: #fff;">{fmt_entero(utilidad_n)}</strong>
                        </div>
                        <div style="margin-top: 6px;">✔ Correcta.</div>
                    </div>
                    <div style="background: rgba(30,41,59,0.6); border-radius: 12px; padding: 16px 20px; border-left: 4px solid #8b5cf6;">
                        <div style="font-weight: 700; margin-bottom: 8px;">3️⃣ Validación balance final</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 12px; align-items: baseline;">
                            <span>Activo: <strong style="color: #fff;">{fmt_entero(suma_activo)}</strong></span>
                            <span style="color: #64748b;">|</span>
                            <span>Pasivo: <strong style="color: #fff;">{fmt_entero(suma_pasivo)}</strong></span>
                            <span style="margin-left: 8px;">{'✔ Activo = Pasivo' if cuadra_balance else '✘ Descuadrado'}</span>
                        </div>
                    </div>
                </div>
            </div>
            """
                    st.markdown(nota_html, unsafe_allow_html=True)

# --- SECCIÓN 4: VER HISTORIAL (Sprint E) ---
elif opcion == "Ver historial":
    st.markdown('<p class="hero-title">Ver historial</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-hero">Consulta todas las cargas de balance y análisis de renta registrados.</p>', unsafe_allow_html=True)

    actividades_h = db.obtener_ultimas_actividades(limite=1)
    if not actividades_h:
        st.info("No hay historial aún. Conectá Supabase y usá *Cargar Balance* o *Análisis de Renta* para generar registros.")
    else:
        with st.container(border=True):
            col_tipo, col_desde, col_hasta = st.columns(3)
            with col_tipo:
                filtro_tipo = st.selectbox(
                    "Tipo",
                    ["Todos", "Carga de balance", "Análisis de Renta"],
                    key="historial_tipo",
                )
            with col_desde:
                filtro_desde = st.date_input("Desde", value=None, key="historial_desde")
            with col_hasta:
                filtro_hasta = st.date_input("Hasta", value=None, key="historial_hasta")

        tipo_val = None
        if filtro_tipo == "Carga de balance":
            tipo_val = "carga_balance"
        elif filtro_tipo == "Análisis de Renta":
            tipo_val = "analisis_renta"

        fecha_desde_str = None
        fecha_hasta_str = None
        if filtro_desde:
            fecha_desde_str = filtro_desde.isoformat() + "T00:00:00Z"
        if filtro_hasta:
            fecha_hasta_str = filtro_hasta.isoformat() + "T23:59:59Z"

        lista_h = db.obtener_actividades_filtradas(
            tipo=tipo_val,
            fecha_desde=fecha_desde_str,
            fecha_hasta=fecha_hasta_str,
            limite=500,
        )

        if not lista_h:
            st.warning("No hay registros con los filtros elegidos.")
        else:
            ZONA_CHILE_H = ZoneInfo("America/Santiago")
            filas = []
            for a in lista_h:
                fecha_raw = a.get("fecha")
                try:
                    if isinstance(fecha_raw, str) and "T" in fecha_raw:
                        d = datetime.fromisoformat(fecha_raw.replace("Z", "+00:00"))
                        if d.tzinfo is None:
                            d = d.replace(tzinfo=timezone.utc)
                        fecha_str = d.astimezone(ZONA_CHILE_H).strftime("%d/%m/%Y %H:%M")
                    else:
                        fecha_str = str(fecha_raw)[:16] if fecha_raw else "—"
                except Exception:
                    fecha_str = str(fecha_raw)[:16] if fecha_raw else "—"
                tipo_label = "Carga" if a.get("tipo") == "carga_balance" else "Análisis Renta"
                desc = (a.get("descripcion") or "—").strip() or "—"
                rc = a.get("resultado_contable")
                rli = a.get("rli")
                imp = a.get("impuesto")
                regimen = (a.get("regimen") or "—").strip() or "—"
                filas.append({
                    "Fecha": fecha_str,
                    "Tipo": tipo_label,
                    "Descripción": desc,
                    "Resultado": fmt_entero(rc) if rc is not None else "—",
                    "RLI": fmt_entero(rli) if rli is not None else "—",
                    "Impuesto": fmt_entero(imp) if imp is not None else "—",
                    "Régimen": regimen,
                })
            df_hist = pd.DataFrame(filas)
            st.dataframe(df_hist, use_container_width=True, height=min(400, 50 + 35 * len(filas)))
            buf_csv = io.StringIO()
            df_hist.to_csv(buf_csv, index=False, sep=";", decimal=",")
            buf_csv.seek(0)
            st.download_button(
                label="📥 Exportar CSV",
                data=buf_csv.getvalue(),
                file_name="historial_actividad.csv",
                mime="text/csv",
                key="download_historial",
            )





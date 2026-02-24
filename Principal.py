import io
import streamlit as st
import pandas as pd
import plotly.express as px

# Importamos las funciones de nuestros módulos
#from modulos.lector_contable import procesar_balance_8_columnas, detectar_gastos_rechazados
from modulos.calculos_renta import calcular_rli_basica 
from modulos.asistente_ia import generar_explicacion_renta 
from modulos.lector_contable import (
    procesar_balance_8_columnas,
    detectar_gastos_rechazados,
    validar_y_calcular_resultado,
    balance_8_columnas_para_display,
    validar_debe_haber_cuadra,
    validar_activo_igual_pasivo,
    _nombre_columna_codigo,
)

# Configuración de página
st.set_page_config(page_title="DaddyBalance v1.0", layout="wide", initial_sidebar_state="expanded")

# --- SISTEMA DE SEGURIDAD ---
def check_password():
    def password_entered():
        if st.session_state["password"] == "DADDY2026": 
            st.session_state["password_correct"] = True
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
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: #0b0e14;
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

    .stDataFrame {
        border-radius: 20px !important;
        overflow: visible !important;
    }
    div[data-testid="stDataFrame"] {
        padding-bottom: 16px !important;
    }
    div[data-testid="stDataFrame"] > div {
        overflow: hidden;
        border-radius: 12px;
    }
    
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
    opcion = st.selectbox("Seleccione Función", ["Inicio", "Cargar Balance", "Análisis de Renta"], label_visibility="collapsed")
    st.markdown("---")
    st.info("💡 **D3**: Tasa 10% s/ RLI\n\n💡 **D8**: Atribuido a socios")

# --- SECCIÓN 1: INICIO ---
if opcion == "Inicio":
    st.markdown('<p class="hero-title">Dashboard Global</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-hero">Estado actual de su cartera contable y auditoría automatizada.</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Empresas Activas", "1", "Empresa de Prueba")
    with col2:
        st.metric("Revisiones Pendientes", "0", "Filtros OK")
    with col3:
        st.metric("Eficiencia Fiscal", "94%", "+2.1% optimización")
    
    st.markdown('<p class="section-header-god">🚀 Actividad Reciente</p>', unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("""
        * ✅ **Auditoría:** Balance procesado exitosamente.
        * 🤖 **Asistente:** Informe de RLI generado.
        * 📁 **Archivo:** Nuevo balance detectado en sistema.
        """)

# --- SECCIÓN 2: CARGAR BALANCE ---
elif opcion == "Cargar Balance":
    st.markdown('<p class="hero-title">Carga de Datos</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-hero">Importación masiva de balances de 8 columnas.</p>', unsafe_allow_html=True)
    
    with st.container(border=True):
        archivo_subido = st.file_uploader("Arrastra el archivo Excel aquí", type=["xlsx"], key="carga_balance")
    
    if archivo_subido:
        df = procesar_balance_8_columnas(archivo_subido)
        if not isinstance(df, pd.DataFrame):
            st.error(df)
        else:
            df, utilidad = validar_y_calcular_resultado(df)
            if utilidad > 0:
                st.success(f"✅ Utilidad del Ejercicio: $ {utilidad:,.0f}")
            elif utilidad < 0:
                st.warning(f"⚠ Pérdida del Ejercicio: $ {abs(utilidad):,.0f}")
            else:
                st.success("✅ Utilidad del Ejercicio = 0")
            # Grilla: DEBE/HABER desde DEBITOS/CREDITOS si existen, sino conservar o 0
            df = df.copy()
            if "DEBE" not in df.columns:
                df["DEBE"] = df["DEBITOS"] if "DEBITOS" in df.columns else 0
            if "HABER" not in df.columns:
                df["HABER"] = df["CREDITOS"] if "CREDITOS" in df.columns else 0
            columnas_orden = [
                "CODIGO", "CUENTA", "DEBE", "HABER", "DEUDOR", "ACREEDOR", "ACTIVO", "PASIVO", "PERDIDA", "GANANCIA",
            ]
            cols_carga = [c for c in columnas_orden if c in df.columns]
            df_carga = df[cols_carga].copy()
            nombres_carga = {
                "CODIGO": "CÓDIGO", "CUENTA": "CUENTA", "DEBE": "DEBE", "HABER": "HABER",
                "DEUDOR": "DEUDOR", "ACREEDOR": "ACREEDOR", "ACTIVO": "ACTIVO", "PASIVO": "PASIVO",
                "PERDIDA": "PÉRDIDA", "GANANCIA": "GANANCIA",
            }
            df_carga = df_carga.rename(columns={c: nombres_carga[c] for c in cols_carga if c in nombres_carga})
            def _miles_punto(val):
                if pd.isna(val):
                    return ""
                try:
                    return f"{int(float(val)):,.0f}".replace(",", ".")
                except (ValueError, TypeError):
                    return str(val)
            nums_carga = df_carga.select_dtypes(include=["number"]).columns
            col_cod = "CÓDIGO" if "CÓDIGO" in df_carga.columns else None
            cols_fmt = [c for c in nums_carga if c != col_cod]
            fmt_carga = {c: _miles_punto for c in cols_fmt}
            st.markdown(
                "<style>div[data-testid='stDataFrame'] { padding-bottom: 12px; overflow: visible !important; }"
                "div[data-testid='stDataFrame'] > div { border-radius: 12px; overflow: hidden; }</style>",
                unsafe_allow_html=True,
            )
            # Altura según filas cargadas: 9 filas → 9 visibles, 5 filas → 5 visibles
            n_filas_carga = len(df_carga)
            altura_carga = 48 + 34 * n_filas_carga
            altura_carga = max(180, min(altura_carga, 550))
            st.dataframe(
                df_carga.style.format(fmt_carga),
                use_container_width=True,
                height=int(altura_carga),
            )

# --- SECCIÓN 3: ANÁLISIS DE RENTA (DISEÑO REFINADO) ---
elif opcion == "Análisis de Renta":
    st.markdown('<p class="hero-title">Análisis de Renta Líquida Imponible</p>', unsafe_allow_html=True)
    
    # 1. Selección y Carga (mismo bloque, compacto y alineado)
    st.markdown("""
    <style>
    /* Bloque Análisis Renta: contenedor con borde y columnas alineadas */
    div[data-testid="stVerticalBlock"]:has(.stSelectbox):has(.stFileUploader) {
        gap: 0.5rem;
    }
    div[data-testid="stVerticalBlock"]:has(.stSelectbox):has(.stFileUploader) [data-testid="column"] {
        min-height: 88px; display: flex; flex-direction: column;
    }
    div[data-testid="stVerticalBlock"]:has(.stSelectbox):has(.stFileUploader) .stSelectbox label,
    div[data-testid="stVerticalBlock"]:has(.stSelectbox):has(.stFileUploader) .stFileUploader label {
        font-size: 0.9rem !important; font-weight: 600 !important; color: #94a3b8 !important;
        margin-bottom: 0.35rem !important;
    }
    div[data-testid="stVerticalBlock"]:has(.stSelectbox):has(.stFileUploader) .stSelectbox [data-testid="stSelectbox"] {
        padding: 0.35rem 0 0.5rem 0;
    }
    div[data-testid="stVerticalBlock"]:has(.stSelectbox):has(.stFileUploader) .stFileUploader [data-testid="stFileUploader"] section {
        padding: 0.85rem 1.1rem !important; min-height: 68px !important; border-radius: 12px;
    }
    </style>
    """, unsafe_allow_html=True)
    with st.container(border=True):
        col_reg, col_file = st.columns([1, 2])
        with col_reg:
            regimen_sel = st.selectbox("Seleccione el Régimen Tributario:", 
                                      ["Propyme General (14 D3)", "Propyme Transparente (14 D8)"],
                                      key="regimen_renta")
        with col_file:
            archivo_renta = st.file_uploader("Sube el balance para el cálculo", type=["xlsx"], key="archivo_renta")
    
    if archivo_renta:
        df_renta = procesar_balance_8_columnas(archivo_renta)
        
        if isinstance(df_renta, pd.DataFrame):
            resultados = calcular_rli_basica(df_renta, regimen=regimen_sel)
            detalle_gastos = detectar_gastos_rechazados(df_renta)

            # --- 2. TARJETAS DE MÉTRICAS (mismo tamaño, texto y valores compactos) ---
            st.markdown("---")
            def _card_fmt(n):
                return f"{n:,.0f}".replace(",", ".")
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
                    <div class="value">$ {_card_fmt(r['resultado_contable'])}</div>
                    <div class="detail">&nbsp;</div>
                </div>
                <div class="metric-card">
                    <div class="label">(+) Agregados (Gastos)</div>
                    <div class="value">$ {_card_fmt(r['total_agregados'])}</div>
                    <div class="detail" style="color:#ef4444;">↑ Gasto Rechazado</div>
                </div>
                <div class="metric-card">
                    <div class="label">RLI Estimada</div>
                    <div class="value">$ {_card_fmt(r['rli_estimada'])}</div>
                    <div class="detail" style="color:#10b981;">↑ Base Imponible</div>
                </div>
                <div class="metric-card">
                    <div class="label">Impuesto IDPC</div>
                    <div class="value">$ {_card_fmt(r['impuesto_pagar'])}</div>
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
                    st.plotly_chart(fig, use_container_width=True)

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
                    st.plotly_chart(fig_bar, use_container_width=True)

            # --- 4. CONSULTOR IA ---
            st.markdown("### 🤖 Consultor DaddyBalance")
            explicacion = generar_explicacion_renta(resultados, detalle_gastos)
            st.markdown(f"<div class='ai-box-premium'>{explicacion}</div>", unsafe_allow_html=True)

            # --- 5. GRILLA DE AUDITORÍA ---
            st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
            st.markdown("<h3 style='margin-bottom: 0;'>📊 Grilla de Auditoría</h3>", unsafe_allow_html=True)
            # 1. Validar igualdad Debe/Haber (balance de comprobación)
            cuadra_debe_haber, suma_debe, suma_haber = validar_debe_haber_cuadra(df_renta)
            if not cuadra_debe_haber:
                st.error(
                    f"⚠️ Balance de comprobación no cuadra: Suma DEBE = $ {suma_debe:,.0f} | "
                    f"Suma HABER = $ {suma_haber:,.0f}"
                )
            # 2. Clasificar (activo=deudor 1xx, pasivo=acreedor 2xx/3xx, perdida=deudor 4/5, ganancia=acreedor 6/7/8)
            # 3. Calcular utilidad y agregar fila resultado
            df_grilla = balance_8_columnas_para_display(df_renta.copy())
            df_grilla, _ = validar_y_calcular_resultado(df_grilla)
            # DEBE/HABER = movimientos; usar DEBITOS/CREDITOS si existen, sino DEBE/HABER del Excel, sino 0
            if "DEBE" not in df_grilla.columns:
                df_grilla["DEBE"] = df_grilla["DEBITOS"] if "DEBITOS" in df_grilla.columns else 0
            if "HABER" not in df_grilla.columns:
                df_grilla["HABER"] = df_grilla["CREDITOS"] if "CREDITOS" in df_grilla.columns else 0
            # Orden y conjunto de columnas: CÓDIGO, CUENTA, DEBE, HABER, DEUDOR, ACREEDOR, ACTIVO, PASIVO, PÉRDIDA, GANANCIA
            columnas_grilla_orden = [
                "CODIGO", "CUENTA", "DEBE", "HABER", "DEUDOR", "ACREEDOR", "ACTIVO", "PASIVO", "PERDIDA", "GANANCIA",
            ]
            columnas_grilla = [c for c in columnas_grilla_orden if c in df_grilla.columns]
            df_grilla = df_grilla[columnas_grilla].copy()
            # Encabezados tal como solicitado (PÉRDIDA con tilde)
            nombres_grilla = {
                "CODIGO": "CÓDIGO", "CUENTA": "CUENTA", "DEBE": "DEBE", "HABER": "HABER",
                "DEUDOR": "DEUDOR", "ACREEDOR": "ACREEDOR", "ACTIVO": "ACTIVO", "PASIVO": "PASIVO",
                "PERDIDA": "PÉRDIDA", "GANANCIA": "GANANCIA",
            }
            renombrar = {c: nombres_grilla[c] for c in columnas_grilla if c in nombres_grilla}
            df_show = df_grilla.rename(columns=renombrar)
            # Formato: miles con punto (ej. 4.906.708), sin símbolo $
            def formatear_miles_punto(val):
                if pd.isna(val):
                    return ""
                try:
                    return f"{int(float(val)):,.0f}".replace(",", ".")
                except (ValueError, TypeError):
                    return str(val)
            columnas_numericas_show = df_show.select_dtypes(include=["number"]).columns
            col_codigo_show = "CÓDIGO" if "CÓDIGO" in df_show.columns else None
            columnas_moneda_show = [c for c in columnas_numericas_show if c != col_codigo_show]
            formato_final = {c: formatear_miles_punto for c in columnas_moneda_show}

            codigos_rechazo = set()
            if detalle_gastos is not None and not detalle_gastos.empty:
                col_codigo_dg = _nombre_columna_codigo(detalle_gastos.columns)
                if col_codigo_dg:
                    codigos_rechazo = set(str(c) for c in detalle_gastos[col_codigo_dg].dropna())

            def highlight_gr(row):
                val_codigo = str(row.get(col_codigo_show, "")) if col_codigo_show else ""
                if val_codigo in codigos_rechazo and val_codigo:
                    return ["background-color: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444;"] * len(row)
                return [""] * len(row)

            st.markdown(
                "<style>div[data-testid='stDataFrame'] { padding-bottom: 20px !important; margin-bottom: 8px; margin-top: -8px !important; }</style>",
                unsafe_allow_html=True,
            )
            # Altura exacta: dibujar solo las filas cargadas (9 filas → 9 filas visibles, 5 → 5)
            n_filas = len(df_show)
            alto_cabecera = 48
            alto_por_fila = 34
            altura_grilla = alto_cabecera + alto_por_fila * n_filas
            altura_grilla = max(180, min(altura_grilla, 550))  # mínimo 180px; si muchas filas, scroll desde ~15
            st.dataframe(
                df_show.style.apply(highlight_gr, axis=1).format(formato_final),
                use_container_width=True,
                height=int(altura_grilla),
            )
            # 6. Validar balance final: sum(activo) == sum(pasivo)
            suma_activo, suma_pasivo, cuadra_balance = validar_activo_igual_pasivo(df_grilla)
            if cuadra_balance:
                st.success(f"✅ Balance correcto (Activo = Pasivo: $ {suma_activo:,.0f})")
            else:
                st.error(
                    f"⚠️ Balance 8 columnas descuadrado: Suma ACTIVO = $ {suma_activo:,.0f} | "
                    f"Suma PASIVO = $ {suma_pasivo:,.0f} | Diferencia = $ {abs(suma_activo - suma_pasivo):,.0f}"
                )
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
            total_debe_n = int(df_grilla["DEBE"].sum()) if "DEBE" in df_grilla.columns else 0
            total_haber_n = int(df_grilla["HABER"].sum()) if "HABER" in df_grilla.columns else 0
            total_ganancia_n = int(df_grilla["GANANCIA"].sum()) if "GANANCIA" in df_grilla.columns else 0
            total_perdida_n = int(df_grilla["PERDIDA"].sum()) if "PERDIDA" in df_grilla.columns else 0
            utilidad_n = total_ganancia_n - total_perdida_n

            def _fmt(n):
                return f"{n:,}".replace(",", ".")

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
                            <span>Total Debe <strong style="color: #fff;">{_fmt(total_debe_n)}</strong></span>
                            <span style="color: #64748b;">|</span>
                            <span>Total Haber <strong style="color: #fff;">{_fmt(total_haber_n)}</strong></span>
                            <span style="margin-left: 8px;">{'✔ Debe = Haber' if cuadra_debe_haber else '✘ No cuadra'}</span>
                        </div>
                    </div>
                    <div style="background: rgba(30,41,59,0.6); border-radius: 12px; padding: 16px 20px; border-left: 4px solid #10b981;">
                        <div style="font-weight: 700; margin-bottom: 8px;">2️⃣ Cálculo de utilidad</div>
                        <div style="color: #94a3b8; font-size: 0.95rem;">
                            Ganancias: <strong style="color: #10b981;">{_fmt(total_ganancia_n)}</strong> &nbsp;&nbsp;−&nbsp;&nbsp;
                            Pérdidas: <strong style="color: #f59e0b;">{_fmt(total_perdida_n)}</strong>
                            &nbsp;&nbsp;=&nbsp;&nbsp; Utilidad: <strong style="color: #fff;">{_fmt(utilidad_n)}</strong>
                        </div>
                        <div style="margin-top: 6px;">✔ Correcta.</div>
                    </div>
                    <div style="background: rgba(30,41,59,0.6); border-radius: 12px; padding: 16px 20px; border-left: 4px solid #8b5cf6;">
                        <div style="font-weight: 700; margin-bottom: 8px;">3️⃣ Validación balance final</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 12px; align-items: baseline;">
                            <span>Activo: <strong style="color: #fff;">{_fmt(suma_activo)}</strong></span>
                            <span style="color: #64748b;">|</span>
                            <span>Pasivo: <strong style="color: #fff;">{_fmt(suma_pasivo)}</strong></span>
                            <span style="margin-left: 8px;">{'✔ Activo = Pasivo' if cuadra_balance else '✘ Descuadrado'}</span>
                        </div>
                    </div>
                </div>
            </div>
            """
            st.markdown(nota_html, unsafe_allow_html=True)




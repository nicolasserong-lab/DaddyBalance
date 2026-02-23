# C:\Users\nicol\Desktop\DaddyBalance\Principal.py

import streamlit as st
import pandas as pd
import os

# Importamos las funciones de nuestros módulos
from modulos.lector_contable import procesar_balance_8_columnas, detectar_gastos_rechazados
from modulos.calculos_renta import calcular_rli_basica 
from modulos.asistente_ia import generar_explicacion_renta 

st.set_page_config(page_title="DaddyBalance v1.0", layout="wide")

st.title("👨‍💼 DaddyBalance: Asistente Inteligente de Operación Renta")

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    [data-testid="stMetric"] {
        background-color: #1e2130;
        border: 1px solid #3e445b;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        min-height: 140px; 
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    [data-testid="stMetricLabel"] {
        color: #a0aec0 !important;
        font-weight: bold;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGACIÓN ---
st.sidebar.header("Menú de Navegación")
opcion = st.sidebar.selectbox("Seleccione una función:", ["Inicio", "Cargar Balance", "Análisis de Renta"])
st.sidebar.markdown("---")
st.sidebar.info(f"💡 **Tip Contable:** Recuerda que las multas fiscales siempre son agregados a la RLI.")

# --- SECCIÓN 1: INICIO ---
if opcion == "Inicio":
    st.subheader("Bienvenido al sistema para el Contador Moderno")
    st.write("Este sistema ayuda a automatizar la revisión de balances y declaraciones.")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Empresas Activas", "1")
    col2.metric("Revisiones Pendientes", "0")
    col3.metric("Errores Detectados", "0")

# --- SECCIÓN 2: CARGAR BALANCE ---
elif opcion == "Cargar Balance":
    st.subheader("Subida de Documentos Contables")
    archivo_subido = st.file_uploader("Arrastra tu Balance Excel aquí", type=["xlsx"], key="carga_balance")
    
    if archivo_subido is not None:
        df = procesar_balance_8_columnas(archivo_subido)
        if isinstance(df, pd.DataFrame):
            st.success("¡Balance cargado!")
            # Formateo rápido para la vista previa
            columnas_num = df.select_dtypes(include=['number']).columns
            st.dataframe(df.head(10).style.format({col: "$ {:,.0f}" for col in columnas_num}))
            
            if st.button("🔍 Analizar Gastos Rechazados"):
                sospechosos = detectar_gastos_rechazados(df)
                if not sospechosos.empty:
                    st.warning("Se detectaron posibles Gastos Rechazados:")
                    st.table(sospechosos.style.format({col: "$ {:,.0f}" for col in sospechosos.select_dtypes(include=['number']).columns}))
                else:
                    st.info("No se detectaron palabras clave de gastos rechazados.")
        else:
            st.error(df)

# --- SECCIÓN 3: ANÁLISIS DE RENTA ---
elif opcion == "Análisis de Renta":
    st.subheader("Cálculo Estimado de Renta Líquida Imponible (RLI)")
    
    archivo_renta = st.file_uploader("Sube el balance para el cálculo de Renta", type=["xlsx"], key="renta_upload")
    
    if archivo_renta is not None:
        df_renta = procesar_balance_8_columnas(archivo_renta)
        
        if isinstance(df_renta, pd.DataFrame):
            # 1. Cálculos base
            resultados = calcular_rli_basica(df_renta)
            detalle_gastos = detectar_gastos_rechazados(df_renta)
            
            # 2. Tarjetas de métricas superiores
            metrica1, metrica2, metrica3 = st.columns(3)
            metrica1.metric("Utilidad Financiera", f"$ {resultados['resultado_contable']:,.0f}")
            metrica2.metric("(+) Agregados (Gastos)", f"$ {resultados['total_agregados']:,.0f}", delta="Gasto Rechazado", delta_color="inverse")
            metrica3.metric("RLI Estimada", f"$ {resultados['rli_estimada']:,.0f}", delta="Base Imponible")
            
            st.markdown("---")
            
            # 3. Asistente Inteligente
            st.markdown("### 🤖 Consultor DaddyBalance")
            explicacion = generar_explicacion_renta(resultados, detalle_gastos)
            
            st.markdown(f"""
                <div style='background-color: #1e2130; padding: 20px; border-radius: 12px; border-left: 6px solid #4CAF50; color: white; line-height: 1.6;'>
                    {explicacion}
                </div>
            """, unsafe_allow_html=True)

            st.divider()

            # 4. Tabla Maestra con Resaltado "Hardcoded" y Formato CLP
            st.write("### 📊 Grilla de Balance con Detección Automática")
            
            # Identificar columnas numéricas
            cols_num = df_renta.select_dtypes(include=['number']).columns
            formato_clp = {col: "$ {:,.0f}" for col in cols_num}

            # Lista de códigos que deben resaltarse (obtenida de la detección)
            if detalle_gastos is not None and 'Código' in detalle_gastos.columns:
                codigos_a_resaltar = set(str(c) for c in detalle_gastos['Código'].dropna())
            else:
                codigos_a_resaltar = set()

            def estilo_final(row):
                codigo = str(row.get('Código', ''))
                # Si el código de la fila está en nuestra lista de rechazados
                if codigo in codigos_a_resaltar:
                    # Aplicamos un rojo fuerte con texto blanco y !important para forzar a Streamlit
                     return [
                        'background-color: #9e1b1b !important; color: white !important; font-weight: bold !important;'
                        ] * len(row)
                return [''] * len(row)

            # Renderizar con la configuración de fuerza bruta para el color
            st.dataframe(
                df_renta.style.apply(estilo_final, axis=1).format(formato_clp),
                use_container_width=True,
                height=500
            )
            
            st.info("💡 Las filas en rojo intenso corresponden a gastos no deducibles detectados automáticamente.")

            # 5. Herramientas finales
            st.download_button(label="📥 Descargar Informe para Cliente", 
                               data=explicacion, 
                               file_name="Informe_RLI_DaddyBalance.txt")
        else:
            st.error("Error al procesar el archivo.")
# C:\Users\nicol\Desktop\DaddyBalance\modulos\asistente_ia.py
import streamlit as st
from groq import Groq  # <-- Cambiamos la librería

def _normalizar_nombre_columna(nombre):
    """Normaliza nombre de columna (mayúsculas, sin tildes)."""
    s = str(nombre).strip().upper()
    for viejo, nuevo in [("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U")]:
        s = s.replace(viejo, nuevo)
    return s

def _columna_codigo_en_dataframe(df):
    """Busca la columna CODIGO."""
    if df is None or df.empty:
        return None
    for c in df.columns:
        if _normalizar_nombre_columna(c) == "CODIGO":
            return c
    return None

def generar_explicacion_renta(resultados, detalle_agregados=None):
    """
    Usa el motor de Groq (Llama 3) para generar el análisis experto.
    """
    # 1. Configuración del cliente Groq (Usando la Key de tu proyecto Aura)
    # Asegúrate de poner esta KEY en tu secrets.toml como GROQ_API_KEY
    api_key = st.secrets.get("GROQ_API_KEY")
    
    if not api_key:
        return "⚠️ Error: No se encontró GROQ_API_KEY en .streamlit/secrets.toml"

    try:
        client = Groq(api_key=api_key)
        
        # 2. Datos para el contexto
        utilidad = resultados["resultado_contable"]
        agregados = resultados["total_agregados"]
        rli = resultados["rli_estimada"]
        impuesto = resultados["impuesto_pagar"]
        tasa = resultados.get("tasa_aplicada", 0) * 100
        
        cuentas_info = ""
        if detalle_agregados is not None and not detalle_agregados.empty:
            col_cod = _columna_codigo_en_dataframe(detalle_agregados)
            for _, fila in detalle_agregados.iterrows():
                cod = fila[col_cod] if col_cod else "N/A"
                cuentas_info += f"- Cuenta: {fila['CUENTA']} (Código: {cod})\n"

        # 3. Prompt al estilo DaddyBalance
        prompt_sistema = """Eres 'DaddyBalance AI', un consultor tributario chileno senior.
        Tu tono es técnico, directo y profesional. Analizas la Renta Líquida Imponible (RLI).
        Formatea con Markdown y usa negritas para valores monetarios."""

        prompt_usuario = f"""Realiza un resumen ejecutivo:
        - Utilidad Contable: $ {utilidad:,.0f}
        - Gastos Rechazados (Agregados): $ {agregados:,.0f}
        - RLI Final: $ {rli:,.0f}
        - Impuesto Estimado: $ {impuesto:,.0f} (Tasa {tasa}%)
        
        Cuentas detectadas:
        {cuentas_info if cuentas_info else "Ninguna."}
        
        Estructura: 1. Diagnóstico, 2. Impacto de Agregados, 3. Recomendación Cierre."""

        # 4. Llamada al modelo Llama 3 (el mismo de tu proyecto Aura)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario},
            ],
            temperature=0.3, # Baja temperatura para mayor precisión técnica
            max_tokens=1000
        )

        return completion.choices[0].message.content

    except Exception as e:
        return f"""**Análisis (Modo Local):**
        Resultado Contable: $ {utilidad:,.0f} | RLI: $ {rli:,.0f}
        *(Error con Groq: {str(e)})*"""


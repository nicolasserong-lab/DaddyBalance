"""
Configuración de reglas de renta (gastos rechazados para RLI).
Los patrones se leen de .streamlit/secrets.toml (GASTOS_RECHAZADOS) o se usa lista por defecto.
"""
import re


# Patrones por defecto si no se configura nada en secrets (comportamiento histórico)
PATRONES_GASTOS_RECHAZADOS_DEFAULT = ["MULTA", "INTERESES MORATORIOS"]


def get_patrones_gastos_rechazados():
    """
    Devuelve la lista de patrones de nombres de cuenta que se consideran gastos rechazados.
    Origen: st.secrets["GASTOS_RECHAZADOS"] (string separado por comas o lista en TOML).
    Si no está configurado, usa PATRONES_GASTOS_RECHAZADOS_DEFAULT.
    """
    try:
        import streamlit as st
        raw = st.secrets.get("GASTOS_RECHAZADOS")
    except Exception:
        raw = None

    if raw is None:
        return list(PATRONES_GASTOS_RECHAZADOS_DEFAULT)

    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    return [x.strip() for x in str(raw).split(",") if x.strip()]


def regex_gastos_rechazados(patrones=None):
    """
    Construye la expresión regular para filtrar cuentas por nombre.
    patrones: lista de strings; si es None, usa get_patrones_gastos_rechazados().
    """
    if patrones is None:
        patrones = get_patrones_gastos_rechazados()
    if not patrones:
        return ""
    return "|".join(re.escape(p) for p in patrones)

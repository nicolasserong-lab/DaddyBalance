"""
Sprint B: Módulo de persistencia con Supabase.
Todas las operaciones de lectura/escritura de la tabla actividad pasan por aquí.
Si SUPABASE_URL o SUPABASE_KEY no están configurados, las funciones no fallan: retornan vacío o None.
"""
import os
from datetime import datetime
from typing import Optional

# Cliente cacheado (una sola conexión por sesión)
_client = None


def _get_url_key():
    """Obtiene URL y KEY de Streamlit secrets, variables de entorno o .streamlit/secrets.toml."""
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    if url and key:
        return url, key
    try:
        import streamlit as st
        url = str(st.secrets.get("SUPABASE_URL") or "").strip()
        key = str(st.secrets.get("SUPABASE_KEY") or "").strip()
        if url and key:
            return url, key
    except Exception:
        pass
    try:
        import tomli
        raiz = os.getcwd()
        path = os.path.join(raiz, ".streamlit", "secrets.toml")
        if not os.path.isfile(path):
            path = os.path.join(os.path.dirname(__file__), "..", ".streamlit", "secrets.toml")
            path = os.path.abspath(path)
        if os.path.isfile(path):
            with open(path, "rb") as f:
                s = tomli.load(f)
            url = str(s.get("SUPABASE_URL") or "").strip()
            key = str(s.get("SUPABASE_KEY") or "").strip()
            if url and key:
                return url, key
    except Exception:
        pass
    return "", ""


def get_client():
    """Devuelve el cliente Supabase o None si no está configurado."""
    global _client
    if _client is not None:
        return _client
    url, key = _get_url_key()
    if not url or not key:
        return None
    try:
        from supabase import create_client as _create
        _client = _create(url, key)
        return _client
    except Exception:
        return None


def guardar_carga_balance(
    fecha: Optional[datetime] = None,
    descripcion: str = "",
    archivo_guardado: Optional[str] = None,
    resultado_contable: Optional[int] = None,
) -> bool:
    """
    Registra una carga de balance en la tabla actividad.
    Retorna True si se guardó bien, False si no hay cliente o falló.
    """
    client = get_client()
    if client is None:
        return False
    try:
        data = {
            "tipo": "carga_balance",
            "fecha": (fecha or datetime.utcnow()).isoformat(),
            "descripcion": descripcion or "Carga de balance",
            "archivo_guardado": archivo_guardado,
            "resultado_contable": resultado_contable,
        }
        client.table("actividad").insert(data).execute()
        return True
    except Exception:
        return False


def guardar_analisis_renta(
    fecha: Optional[datetime] = None,
    descripcion: str = "",
    resultado_contable: Optional[int] = None,
    rli: Optional[int] = None,
    impuesto: Optional[int] = None,
    regimen: Optional[str] = None,
) -> bool:
    """
    Registra un análisis de renta en la tabla actividad.
    Retorna True si se guardó bien, False si no hay cliente o falló.
    """
    client = get_client()
    if client is None:
        return False
    try:
        data = {
            "tipo": "analisis_renta",
            "fecha": (fecha or datetime.utcnow()).isoformat(),
            "descripcion": descripcion or "Análisis de Renta",
            "resultado_contable": resultado_contable,
            "rli": rli,
            "impuesto": impuesto,
            "regimen": regimen,
        }
        client.table("actividad").insert(data).execute()
        return True
    except Exception:
        return False


def obtener_ultimas_actividades(limite: int = 10) -> list:
    """
    Devuelve las últimas actividades (cargas y análisis) ordenadas por fecha descendente.
    Retorna lista de diccionarios. Si no hay cliente o falla, retorna [].
    """
    client = get_client()
    if client is None:
        return []
    try:
        r = client.table("actividad").select("*").order("fecha", desc=True).limit(limite).execute()
        return list(r.data) if r.data else []
    except Exception:
        return []


def obtener_actividades_filtradas(
    tipo: Optional[str] = None,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    limite: int = 500,
) -> list:
    """
    Devuelve actividades con filtros opcionales.
    tipo: None (todas), 'carga_balance' o 'analisis_renta'.
    fecha_desde / fecha_hasta: ISO string o None.
    Retorna lista de diccionarios ordenada por fecha descendente.
    """
    client = get_client()
    if client is None:
        return []
    try:
        q = client.table("actividad").select("*").order("fecha", desc=True).limit(limite)
        if tipo:
            q = q.eq("tipo", tipo)
        if fecha_desde:
            q = q.gte("fecha", fecha_desde)
        if fecha_hasta:
            q = q.lte("fecha", fecha_hasta)
        r = q.execute()
        return list(r.data) if r.data else []
    except Exception:
        return []


def obtener_estadisticas_inicio() -> dict:
    """
    Devuelve estadísticas para la pantalla Inicio:
    - total_cargas: cantidad de registros tipo carga_balance
    - total_analisis: cantidad de registros tipo analisis_renta
    - ultima_rli, ultimo_impuesto: del último analisis_renta (si existe)
    Si no hay cliente o falla, retorna dict con valores en 0/None.
    """
    actividades = obtener_ultimas_actividades(limite=500)
    if not actividades:
        return {
            "total_cargas": 0,
            "total_analisis": 0,
            "ultima_rli": None,
            "ultimo_impuesto": None,
        }
    total_cargas = sum(1 for a in actividades if a.get("tipo") == "carga_balance")
    total_analisis = sum(1 for a in actividades if a.get("tipo") == "analisis_renta")
    ultima_rli = None
    ultimo_impuesto = None
    for a in actividades:
        if a.get("tipo") == "analisis_renta":
            ultima_rli = a.get("rli")
            ultimo_impuesto = a.get("impuesto")
            break
    return {
        "total_cargas": total_cargas,
        "total_analisis": total_analisis,
        "ultima_rli": ultima_rli,
        "ultimo_impuesto": ultimo_impuesto,
    }

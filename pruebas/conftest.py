"""
Fixtures compartidas para las pruebas de DaddyBalance.
"""
import io
import sys
import os

# Raíz del proyecto para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import pytest


class ArchivoFalso:
    """Objeto tipo archivo subido: tiene .name y métodos read/seek/tell para pandas."""
    def __init__(self, bytes_data: bytes, nombre: str = "test.xlsx"):
        self._buf = io.BytesIO(bytes_data)
        self.name = nombre

    def read(self, n=-1):
        return self._buf.read(n)

    def seek(self, pos, whence=io.SEEK_SET):
        return self._buf.seek(pos, whence)

    def tell(self):
        return self._buf.tell()

    def seekable(self):
        return True


def _balance_8_columnas_minimo():
    """DataFrame mínimo válido: Código, Cuenta, Débitos, Créditos, Deudor, Acreedor, Activo, Pasivo, Pérdida, Ganancia. Cuadra."""
    return pd.DataFrame({
        "Código": [101, 102, 301, 401, 601],
        "Cuenta": ["Caja", "Banco", "Capital", "Sueldos", "Ventas"],
        "Débitos": [100, 500, 0, 200, 0],
        "Créditos": [0, 0, 600, 0, 200],
        "Deudor": [100, 500, 0, 200, 0],
        "Acreedor": [0, 0, 600, 0, 200],
        "Activo": [100, 500, 0, 0, 0],
        "Pasivo": [0, 0, 600, 0, 0],
        "Pérdida": [0, 0, 0, 200, 0],
        "Ganancia": [0, 0, 0, 0, 200],
    })


@pytest.fixture
def excel_balance_minimo():
    """Excel válido de 8 columnas que cuadra (Debe=Haber, Activo=Pasivo)."""
    df = _balance_8_columnas_minimo()
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return ArchivoFalso(buf.read(), "balance_minimo.xlsx")


@pytest.fixture
def excel_balance_con_multa_e_intereses():
    """Excel con MULTA e INTERESES MORATORIOS para probar gastos rechazados."""
    df = pd.DataFrame({
        "Código": [501, 502, 601, 401],
        "Cuenta": ["MULTA SII", "INTERESES MORATORIOS", "Ventas", "Sueldos"],
        "Débitos": [2_500_000, 2_500_000, 0, 1_000_000],
        "Créditos": [0, 0, 10_000_000, 0],
        "Deudor": [2_500_000, 2_500_000, 0, 1_000_000],
        "Acreedor": [0, 0, 10_000_000, 0],
        "Activo": [0, 0, 0, 0],
        "Pasivo": [0, 0, 0, 0],
        "Pérdida": [2_500_000, 2_500_000, 0, 1_000_000],
        "Ganancia": [0, 0, 10_000_000, 0],
    })
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return ArchivoFalso(buf.read(), "balance_renta.xlsx")


@pytest.fixture
def excel_vacio():
    """Excel con una hoja vacía (sin filas de datos)."""
    df = pd.DataFrame()
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return ArchivoFalso(buf.read(), "vacio.xlsx")


@pytest.fixture
def archivo_txt():
    """Objeto tipo archivo con extensión .txt (formato no permitido)."""
    return ArchivoFalso(b"contenido cualquiera", "archivo.txt")

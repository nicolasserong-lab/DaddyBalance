"""
Tests del módulo validaciones_carga: formato archivo, contenido, estructura 8 columnas.
"""
import io
import pytest
import pandas as pd

from modulos.validaciones_carga import (
    validar_formato_archivo,
    validar_archivo_tiene_contenido,
    validar_estructura_8_columnas,
    get_solucion_validacion_basica,
    MENSAJE_FORMATO_NO_PERMITIDO,
    MENSAJE_SIN_INFORMACION_VALIDA,
    ESTRUCTURA_VALIDA,
    ESTRUCTURA_NO_VALIDA,
)


class ArchivoConNombre:
    def __init__(self, bytes_data: bytes, nombre: str):
        self._buf = io.BytesIO(bytes_data)
        self.name = nombre

    def read(self, n=-1):
        return self._buf.read(n)

    def seek(self, pos, whence=io.SEEK_SET):
        return self._buf.seek(pos, whence)


class TestValidarFormatoArchivo:
    """validar_formato_archivo."""

    def test_none_devuelve_false(self):
        ok, msg = validar_formato_archivo(None)
        assert ok is False
        assert msg == MENSAJE_FORMATO_NO_PERMITIDO

    def test_txt_devuelve_false(self, archivo_txt):
        ok, msg = validar_formato_archivo(archivo_txt)
        assert ok is False
        assert "Excel" in msg or "xls" in msg.lower()

    def test_xlsx_devuelve_true(self, excel_balance_minimo):
        ok, msg = validar_formato_archivo(excel_balance_minimo)
        assert ok is True
        assert msg is None


class TestValidarArchivoTieneContenido:
    """validar_archivo_tiene_contenido."""

    def test_none_devuelve_false(self):
        ok, msg = validar_archivo_tiene_contenido(None)
        assert ok is False

    def test_excel_con_datos_devuelve_true(self, excel_balance_minimo):
        ok, msg = validar_archivo_tiene_contenido(excel_balance_minimo)
        assert ok is True
        assert msg is None

    def test_excel_vacio_devuelve_false(self, excel_vacio):
        ok, msg = validar_archivo_tiene_contenido(excel_vacio)
        assert ok is False
        assert msg == MENSAJE_SIN_INFORMACION_VALIDA


class TestValidarEstructura8Columnas:
    """validar_estructura_8_columnas."""

    def test_excel_valido_8_columnas_devuelve_valida(self, excel_balance_minimo):
        excel_balance_minimo.seek(0)
        es_valida, texto, detalle = validar_estructura_8_columnas(excel_balance_minimo)
        assert es_valida is True
        assert texto == ESTRUCTURA_VALIDA
        assert detalle is None

    def test_none_devuelve_no_valida(self):
        es_valida, texto, detalle = validar_estructura_8_columnas(None)
        assert es_valida is False
        assert texto == ESTRUCTURA_NO_VALIDA
        assert detalle is not None


class TestGetSolucionValidacionBasica:
    """get_solucion_validacion_basica."""

    def test_formato_tiene_solucion(self):
        sol = get_solucion_validacion_basica(MENSAJE_FORMATO_NO_PERMITIDO)
        assert sol is not None
        assert "Por qué" in sol or "solucionarlo" in sol

    def test_mensaje_desconocido_devuelve_none(self):
        sol = get_solucion_validacion_basica("Mensaje que no existe")
        assert sol is None

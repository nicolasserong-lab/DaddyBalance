"""
Tests del módulo calculos_renta: RLI, agregados, impuesto D3/D8.
"""
import pandas as pd
import pytest

from modulos.lector_contable import balance_8_columnas_para_display, procesar_balance_8_columnas
from modulos.calculos_renta import calcular_rli_basica


class TestCalcularRliBasica:
    """calcular_rli_basica."""

    def test_rli_es_resultado_mas_agregados(self):
        df = pd.DataFrame({
            "CODIGO": [501, 502, 601, 401],
            "CUENTA": ["MULTA SII", "INTERESES MORATORIOS", "Ventas", "Sueldos"],
            "PERDIDA": [2_500_000, 2_500_000, 0, 1_000_000],
            "GANANCIA": [0, 0, 10_000_000, 0],
        })
        r = calcular_rli_basica(df, regimen="Propyme General (14 D3)", patrones=["MULTA", "INTERESES MORATORIOS"])
        assert r["resultado_contable"] == 4_000_000  # 10M - 6M
        assert r["total_agregados"] == 5_000_000
        assert r["rli_estimada"] == 9_000_000
        assert r["impuesto_pagar"] == 900_000  # 10% de 9M
        assert r["tasa_aplicada"] == 0.10

    def test_regimen_d8_impuesto_cero(self):
        df = pd.DataFrame({
            "CUENTA": ["Ventas", "Gastos"],
            "PERDIDA": [0, 1_000_000],
            "GANANCIA": [5_000_000, 0],
        })
        r = calcular_rli_basica(df, regimen="Propyme Transparente (14 D8)")
        assert r["tasa_aplicada"] == 0
        assert r["impuesto_pagar"] == 0
        assert r["rli_estimada"] == 4_000_000

    def test_sin_gastos_rechazados_agregados_cero(self):
        df = pd.DataFrame({
            "CUENTA": ["Ventas", "Sueldos"],
            "PERDIDA": [0, 1_000_000],
            "GANANCIA": [3_000_000, 0],
        })
        r = calcular_rli_basica(df, patrones=[])
        assert r["total_agregados"] == 0
        assert r["rli_estimada"] == r["resultado_contable"]

    def test_desde_excel_con_multa_e_intereses(self, excel_balance_con_multa_e_intereses):
        raw = procesar_balance_8_columnas(excel_balance_con_multa_e_intereses)
        assert isinstance(raw, pd.DataFrame)
        df = balance_8_columnas_para_display(raw)
        r = calcular_rli_basica(df, regimen="Propyme General (14 D3)", patrones=["MULTA", "INTERESES MORATORIOS"])
        assert r["total_agregados"] == 5_000_000
        assert r["rli_estimada"] == r["resultado_contable"] + 5_000_000

"""
Tests del módulo lector_contable: procesar Excel, combinar balances, clasificación, validaciones.
"""
import pandas as pd
import pytest

from modulos.lector_contable import (
    procesar_balance_8_columnas,
    combinar_balances,
    balance_8_columnas_para_display,
    validar_y_calcular_resultado,
    validar_debe_haber_cuadra,
    validar_activo_igual_pasivo,
    detectar_gastos_rechazados,
    limpiar_monto,
)


class TestProcesarBalance:
    """procesar_balance_8_columnas."""

    def test_excel_valido_devuelve_dataframe(self, excel_balance_minimo):
        resultado = procesar_balance_8_columnas(excel_balance_minimo)
        assert isinstance(resultado, pd.DataFrame), "Debe devolver un DataFrame"
        assert not resultado.empty
        assert "CUENTA" in resultado.columns

    def test_excel_valido_tiene_columnas_normalizadas(self, excel_balance_minimo):
        resultado = procesar_balance_8_columnas(excel_balance_minimo)
        assert "DEBE" in resultado.columns or "DEBITOS" in resultado.columns
        assert "HABER" in resultado.columns or "CREDITOS" in resultado.columns
        assert "DEUDOR" in resultado.columns
        assert "ACREEDOR" in resultado.columns

    def test_archivo_nulo_devuelve_mensaje_error(self):
        resultado = procesar_balance_8_columnas(None)
        assert isinstance(resultado, str)
        assert "Error" in resultado

    def test_excel_vacio_devuelve_error(self, excel_vacio):
        resultado = procesar_balance_8_columnas(excel_vacio)
        assert isinstance(resultado, str)
        assert "Error" in resultado


class TestCombinarBalances:
    """combinar_balances."""

    def test_combinar_dos_dataframes_suma_por_cuenta(self, excel_balance_minimo):
        r1 = procesar_balance_8_columnas(excel_balance_minimo)
        assert isinstance(r1, pd.DataFrame)
        # Mismo archivo "duplicado": combinar debe agrupar
        combined = combinar_balances([r1, r1])
        assert isinstance(combined, pd.DataFrame)
        assert len(combined) == len(r1)

    def test_combinar_lista_vacia_devuelve_error(self):
        resultado = combinar_balances([])
        assert isinstance(resultado, str)
        assert "Error" in resultado


class TestBalance8ColumnasParaDisplay:
    """balance_8_columnas_para_display: clasificación por código chileno."""

    def test_clasifica_activo_pasivo_perdida_ganancia(self, excel_balance_minimo):
        raw = procesar_balance_8_columnas(excel_balance_minimo)
        df = balance_8_columnas_para_display(raw)
        assert "ACTIVO" in df.columns
        assert "PASIVO" in df.columns
        assert "PERDIDA" in df.columns
        assert "GANANCIA" in df.columns


class TestValidarYCalcularResultado:
    """validar_y_calcular_resultado: inserta Utilidad/Pérdida del Ejercicio."""

    def test_agrega_fila_utilidad_cuando_ganancia_mayor(self, excel_balance_minimo):
        raw = procesar_balance_8_columnas(excel_balance_minimo)
        df = balance_8_columnas_para_display(raw)
        df_out, utilidad = validar_y_calcular_resultado(df)
        assert "Utilidad del Ejercicio" in df_out["CUENTA"].values or "Pérdida del Ejercicio" in df_out["CUENTA"].values
        assert len(df_out) == len(df) + 1

    def test_utilidad_coincide_con_ganancia_menos_perdida(self, excel_balance_minimo):
        raw = procesar_balance_8_columnas(excel_balance_minimo)
        df = balance_8_columnas_para_display(raw)
        sum_ganancia = df["GANANCIA"].sum() if "GANANCIA" in df.columns else 0
        sum_perdida = df["PERDIDA"].sum() if "PERDIDA" in df.columns else 0
        esperada = sum_ganancia - sum_perdida
        _, utilidad = validar_y_calcular_resultado(df)
        assert utilidad == esperada


class TestValidarDebeHaber:
    """validar_debe_haber_cuadra."""

    def test_balance_cuadrado_devuelve_true(self, excel_balance_minimo):
        raw = procesar_balance_8_columnas(excel_balance_minimo)
        cuadra, s_debe, s_haber = validar_debe_haber_cuadra(raw)
        assert cuadra is True
        assert s_debe == s_haber


class TestValidarActivoPasivo:
    """validar_activo_igual_pasivo."""

    def test_despues_de_cierre_activo_igual_pasivo(self, excel_balance_minimo):
        raw = procesar_balance_8_columnas(excel_balance_minimo)
        df = balance_8_columnas_para_display(raw)
        df, _ = validar_y_calcular_resultado(df)
        suma_activo, suma_pasivo, cuadra = validar_activo_igual_pasivo(df)
        assert cuadra is True, f"Activo={suma_activo} Pasivo={suma_pasivo}"


class TestDetectarGastosRechazados:
    """detectar_gastos_rechazados."""

    def test_detecta_multa_e_intereses_con_patrones_explicitos(self):
        df = pd.DataFrame({
            "CODIGO": [501, 502, 601],
            "CUENTA": ["MULTA SII", "INTERESES MORATORIOS", "VENTAS"],
            "PERDIDA": [2_500_000, 2_500_000, 0],
        })
        detalle = detectar_gastos_rechazados(df, patrones=["MULTA", "INTERESES MORATORIOS"])
        assert len(detalle) == 2
        assert detalle["PERDIDA"].sum() == 5_000_000

    def test_sin_patrones_devuelve_vacio(self):
        df = pd.DataFrame({"CUENTA": ["VENTAS"], "PERDIDA": [100]})
        detalle = detectar_gastos_rechazados(df, patrones=[])
        assert detalle.empty


class TestLimpiarMonto:
    """limpiar_monto (helper)."""

    def test_entero_devuelve_entero(self):
        assert limpiar_monto(1000) == 1000

    def test_float_redondea(self):
        assert limpiar_monto(1000.4) == 1000
        assert limpiar_monto(1000.6) == 1001

    def test_nan_devuelve_cero(self):
        assert limpiar_monto(pd.NA) == 0
        assert limpiar_monto(float("nan")) == 0

    def test_string_numero_parsea(self):
        assert limpiar_monto("1000") == 1000
        # Punto como separador de miles (se elimina): "1.500" -> 1500
        assert limpiar_monto("1.500") == 1500

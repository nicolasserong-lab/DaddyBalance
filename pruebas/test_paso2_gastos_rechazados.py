"""
Pruebas del Paso 2: gastos rechazados configurables.
Ejecutar desde la raíz del proyecto:  python pruebas/test_paso2_gastos_rechazados.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from modulos.lector_contable import (
    detectar_gastos_rechazados,
    balance_8_columnas_para_display,
    procesar_balance_8_columnas,
)
from modulos.calculos_renta import calcular_rli_basica


def test_con_patrones_por_defecto():
    """Con patrones por defecto (MULTA, INTERESES MORATORIOS) se detectan solo esas cuentas."""
    df = pd.DataFrame({
        "CODIGO": [501, 502, 601],
        "CUENTA": ["MULTA SII", "INTERESES MORATORIOS", "VENTAS"],
        "PERDIDA": [2_500_000, 2_500_000, 0],
        "GANANCIA": [0, 0, 1_000],
    })
    detalle = detectar_gastos_rechazados(df, patrones=["MULTA", "INTERESES MORATORIOS"])
    assert len(detalle) == 2, f"Se esperaban 2 filas de gastos rechazados, se obtuvieron {len(detalle)}"
    assert detalle["PERDIDA"].sum() == 5_000_000, f"Suma esperada 5.000.000, se obtuvo {detalle['PERDIDA'].sum()}"
    print("  OK - Patrones por defecto: se detectan MULTA e INTERESES MORATORIOS, suma = 5.000.000")


def test_con_patron_extra():
    """Si agregamos el patrón ARRIENDO, también se marca esa cuenta como rechazada."""
    df = pd.DataFrame({
        "CODIGO": [501, 403, 601],
        "CUENTA": ["MULTA SII", "ARRIENDO LOCAL", "VENTAS"],
        "PERDIDA": [2_500_000, 100_000, 0],
        "GANANCIA": [0, 0, 1_000],
    })
    detalle = detectar_gastos_rechazados(df, patrones=["MULTA", "INTERESES MORATORIOS", "ARRIENDO"])
    assert len(detalle) == 2, f"Se esperaban 2 filas (MULTA + ARRIENDO), se obtuvieron {len(detalle)}"
    assert detalle["PERDIDA"].sum() == 2_600_000, f"Suma esperada 2.600.000, se obtuvo {detalle['PERDIDA'].sum()}"
    print("  OK - Con patrón extra ARRIENDO: se detectan MULTA y ARRIENDO LOCAL, suma = 2.600.000")


def test_calcular_rli_usando_detectar():
    """calcular_rli_basica usa detectar_gastos_rechazados; total_agregados debe coincidir."""
    df = pd.DataFrame({
        "CODIGO": [501, 502, 601, 401],
        "CUENTA": ["MULTA SII", "INTERESES MORATORIOS", "VENTAS", "SUELDOS"],
        "PERDIDA": [2_500_000, 2_500_000, 0, 1_000_000],
        "GANANCIA": [0, 0, 10_000_000, 0],
    })
    resultados = calcular_rli_basica(df, regimen="Propyme General (14 D3)", patrones=["MULTA", "INTERESES MORATORIOS"])
    assert resultados["total_agregados"] == 5_000_000, f"total_agregados esperado 5.000.000, se obtuvo {resultados['total_agregados']}"
    # resultado_contable = 10M (ventas) - 6M (sueldos + 2.5M + 2.5M) = 4M
    assert resultados["resultado_contable"] == 4_000_000
    assert resultados["rli_estimada"] == resultados["resultado_contable"] + 5_000_000  # 9M
    print("  OK - calcular_rli_basica: total_agregados = 5.000.000, RLI = resultado + agregados")


def test_con_excel_real():
    """Opcional: si existe el balance de prueba, procesarlo y verificar agregados."""
    ruta = os.path.join(os.path.dirname(os.path.dirname(__file__)), "documentos", "balance_prueba_consistente.xlsx")
    if not os.path.isfile(ruta):
        print("  (Omitido - no existe documentos/balance_prueba_consistente.xlsx)")
        return
    with open(ruta, "rb") as f:
        raw = procesar_balance_8_columnas(f)
    if isinstance(raw, str):
        print("  (Omitido - el archivo no pudo procesarse)")
        return
    df = balance_8_columnas_para_display(raw)
    if df.empty:
        print("  (Omitido - balance vacío)")
        return
    resultados = calcular_rli_basica(df, regimen="Propyme General (14 D3)", patrones=["MULTA", "INTERESES MORATORIOS"])
    assert resultados["total_agregados"] == 5_000_000, f"En el Excel de prueba se esperaba total_agregados 5.000.000, se obtuvo {resultados['total_agregados']}"
    print("  OK - Excel real: total_agregados = 5.000.000")


if __name__ == "__main__":
    print("Paso 2 - Pruebas de gastos rechazados configurables\n")
    test_con_patrones_por_defecto()
    test_con_patron_extra()
    test_calcular_rli_usando_detectar()
    test_con_excel_real()
    print("\nTodas las pruebas pasaron.")

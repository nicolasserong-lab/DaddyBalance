"""
SPRINT 1 - Validaciones básicas de archivo para Cargar Balance.
SPRINT 2 - Validación de estructura 8 columnas (solo clasificación, no genera balance).
"""
import re
import pandas as pd

MENSAJE_FORMATO_NO_PERMITIDO = (
    "Formato no permitido. Solo se aceptan archivos Excel (.xls, .xlsx)."
)
SOLUCION_FORMATO = (
    "**¿Por qué aparece este mensaje?** El archivo que subió no tiene extensión .xls o .xlsx "
    "(por ejemplo es .txt, .pdf, .csv o otro formato).\n\n"
    "**Cómo solucionarlo:** Guarde o exporte su balance como Excel (.xls o .xlsx) y vuelva a subirlo."
)
MENSAJE_SIN_INFORMACION_VALIDA = (
    "El archivo no contiene información válida."
)
SOLUCION_SIN_INFORMACION = (
    "**¿Por qué aparece este mensaje?** El archivo está vacío, no tiene hojas, o todas las hojas están vacías.\n\n"
    "**Cómo solucionarlo:** Asegúrese de que el Excel tenga al menos una hoja con datos (filas y columnas con contenido)."
)
ESTRUCTURA_VALIDA = "Estructura válida 8 columnas"
ESTRUCTURA_NO_VALIDA = "Estructura no válida"

# Nombres lógicos para balance 8 columnas (normalizados: mayúsculas, sin tildes)
# Grupos de sinónimos para movimientos
_CAMPOS_MOV_DEBITO = {"DEBITOS", "DEBE"}
_CAMPOS_MOV_CREDITO = {"CREDITOS", "HABER"}
_CAMPOS_OTROS_OBLIGATORIOS = {
    "DEUDOR",
    "ACREEDOR",
    "ACTIVO",
    "PASIVO",
    "PERDIDA",
    "GANANCIA",
}
_CAMPOS_OPCIONALES = {"CODIGO", "CUENTA"}
_CAMPOS_NUMERICOS = _CAMPOS_MOV_DEBITO | _CAMPOS_MOV_CREDITO | _CAMPOS_OTROS_OBLIGATORIOS
_REPLAZOS_TILDE = [("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U")]


def _normalizar_nombre_columna(nombre):
    """Normaliza nombre de columna: strip, mayúsculas, sin tildes, espacios colapsados."""
    s = str(nombre).strip().upper()
    for viejo, nuevo in _REPLAZOS_TILDE:
        s = s.replace(viejo, nuevo)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _extension_archivo(nombre_archivo):
    """Devuelve la extensión en minúsculas sin punto, o cadena vacía."""
    if not nombre_archivo or "." not in nombre_archivo:
        return ""
    return nombre_archivo.strip().rsplit(".", 1)[-1].lower()


def validar_formato_archivo(archivo):
    """
    Valida que el archivo sea solo .xls o .xlsx.
    Retorna (True, None) si es válido, o (False, mensaje) si no.
    """
    if archivo is None:
        return False, MENSAJE_FORMATO_NO_PERMITIDO
    nombre = getattr(archivo, "name", "") or ""
    ext = _extension_archivo(nombre)
    if ext not in ("xls", "xlsx"):
        return False, MENSAJE_FORMATO_NO_PERMITIDO
    return True, None


def validar_archivo_tiene_contenido(archivo):
    """
    Valida que el archivo no esté vacío, tenga al menos una hoja y que esa hoja tenga datos.
    Retorna (True, None) si es válido, o (False, mensaje) si no.
    No aplica lógica de 8 columnas; solo verifica que haya contenido legible.
    """
    if archivo is None:
        return False, MENSAJE_SIN_INFORMACION_VALIDA

    nombre = getattr(archivo, "name", "") or ""
    ext = _extension_archivo(nombre)
    if ext not in ("xls", "xlsx"):
        return False, MENSAJE_FORMATO_NO_PERMITIDO

    try:
        if hasattr(archivo, "seek"):
            archivo.seek(0)
        engine = "xlrd" if ext == "xls" else "openpyxl"
        xl = pd.ExcelFile(archivo, engine=engine)
    except Exception:
        return False, MENSAJE_SIN_INFORMACION_VALIDA

    if not xl.sheet_names:
        return False, MENSAJE_SIN_INFORMACION_VALIDA

    for sheet_name in xl.sheet_names:
        try:
            hoja = xl.parse(sheet_name=sheet_name)
        except Exception:
            continue
        if hoja is not None and not hoja.empty:
            return True, None

    return False, MENSAJE_SIN_INFORMACION_VALIDA


def get_solucion_validacion_basica(mensaje):
    """
    Devuelve el texto explicativo "por qué y cómo solucionarlo" para un mensaje de validación básica.
    Si no hay texto asociado, devuelve None.
    """
    soluciones = {
        MENSAJE_FORMATO_NO_PERMITIDO: SOLUCION_FORMATO,
        MENSAJE_SIN_INFORMACION_VALIDA: SOLUCION_SIN_INFORMACION,
    }
    return soluciones.get(mensaje)


def _detalle_generico_estructura():
    return (
        "**¿Por qué aparece este mensaje?** No se pudo leer el archivo o no tiene hojas con datos.\n\n"
        "**Cómo solucionarlo:** Verifique que el archivo sea un Excel (.xls o .xlsx) válido y que tenga al menos una hoja con filas de datos."
    )


def _detalle_columnas_desconocidas(desconocidos):
    cols = ", ".join(sorted(desconocidos)[:5])
    if len(desconocidos) > 5:
        cols += " ..."
    return (
        "**¿Por qué aparece este mensaje?** El archivo tiene columnas que no corresponden a un balance de 8 columnas: "
        f"{cols}.\n\n"
        "**Cómo solucionarlo:** Use solo las columnas permitidas: Débitos/Créditos (o Debe/Haber), Deudor, Acreedor, "
        "Activo, Pasivo, Pérdida, Ganancia; opcionalmente Código y Cuenta. Elimine o renombre columnas que no sean estas."
    )


def _detalle_falta_columna(nombre_legible, opciones):
    return (
        f"**¿Por qué aparece este mensaje?** Falta la columna de movimientos deudores o acreedores: {nombre_legible}.\n\n"
        "**Cómo solucionarlo:** Agregue una columna con uno de estos nombres (o equivalente): "
        f"{', '.join(opciones)}. Aceptamos variantes con tildes o mayúsculas."
    )


def _detalle_faltan_obligatorios(faltantes):
    cols = ", ".join(sorted(faltantes))
    return (
        f"**¿Por qué aparece este mensaje?** Faltan columnas obligatorias del balance: {cols}.\n\n"
        "**Cómo solucionarlo:** Agregue columnas con esos nombres (Deudor, Acreedor, Activo, Pasivo, Pérdida, Ganancia). "
        "Puede usar variantes con tildes o mayúsculas."
    )


def _detalle_cantidad_columnas():
    return (
        "**¿Por qué aparece este mensaje?** El archivo no tiene entre 8 y 10 columnas (las requeridas para un balance de 8 columnas).\n\n"
        "**Cómo solucionarlo:** Asegúrese de tener exactamente las columnas: Débitos (o Debe), Créditos (o Haber), "
        "Deudor, Acreedor, Activo, Pasivo, Pérdida, Ganancia; y opcionalmente Código y/o Cuenta. Ni más ni menos columnas de otro tipo."
    )


def _detalle_valores_no_numericos():
    return (
        "**¿Por qué aparece este mensaje?** En alguna columna de montos (Debe, Haber, Deudor, Acreedor, Activo, Pasivo, Pérdida, Ganancia) "
        "hay texto o caracteres que no son números.\n\n"
        "**Cómo solucionarlo:** Deje solo números en esas columnas (o celdas vacías). Evite texto como \"N/A\", \"-\", \"TOTAL\" o formatos con punto como separador de miles (ej. 29.964.358); use solo dígitos o coma/punto decimal."
    )


def _detalle_suma_debe_haber(suma_debe, suma_haber):
    try:
        s_d = int(round(float(suma_debe)))
        s_h = int(round(float(suma_haber)))
    except (TypeError, ValueError):
        s_d = s_h = 0
    return (
        "**¿Por qué aparece este mensaje?** La suma de la columna Debe (o Débitos) no es igual a la suma de la columna Haber (o Créditos). "
        "En un balance correcto ambas sumas deben coincidir.\n\n"
        f"**Valores detectados:** Suma Debe = {s_d:,}; Suma Haber = {s_h:,}.\n\n"
        "**Cómo solucionarlo:** Revise que cada asiento tenga su contrapartida (Debe = Haber en total). "
        "Si usa punto como separador de miles, el sistema puede interpretar mal los números; use solo dígitos o coma decimal."
    )


def validar_estructura_8_columnas(archivo):
    """
    SPRINT 2: Detecta si el archivo corresponde a un Balance de 8 Columnas.
    Reglas de negocio:
      - Obligatorias (8 lógicas): Débitos, Créditos, Deudor, Acreedor, Activo, Pasivo, Pérdida, Ganancia.
      - Opcionales (2 lógicas): Código, Cuenta.
      - Se aceptan variantes de mayúsculas/minúsculas/tildes (sinónimos se normalizan).
      - Columnas numéricas con valores numéricos.
      - Suma Débitos = Suma Créditos.
    El Excel puede tener entre 8 y 10 columnas físicas, siempre que todas se mapeen
    a estos campos lógicos y estén presentes las 8 obligatorias.
    Retorna (True, ESTRUCTURA_VALIDA, None) o (False, ESTRUCTURA_NO_VALIDA, detalle).
    detalle explica el motivo y cómo solucionarlo.
    """
    if archivo is None:
        return False, ESTRUCTURA_NO_VALIDA, _detalle_generico_estructura()

    nombre = getattr(archivo, "name", "") or ""
    ext = _extension_archivo(nombre)
    if ext not in ("xls", "xlsx"):
        return False, ESTRUCTURA_NO_VALIDA, _detalle_generico_estructura()

    try:
        if hasattr(archivo, "seek"):
            archivo.seek(0)
        engine = "xlrd" if ext == "xls" else "openpyxl"
        xl = pd.ExcelFile(archivo, engine=engine)
    except Exception:
        return False, ESTRUCTURA_NO_VALIDA, _detalle_generico_estructura()

    if not xl.sheet_names:
        return False, ESTRUCTURA_NO_VALIDA, _detalle_generico_estructura()

    hoja = None
    for sheet_name in xl.sheet_names:
        try:
            h = xl.parse(sheet_name=sheet_name)
        except Exception:
            continue
        if h is not None and not h.empty:
            hoja = h
            break

    if hoja is None or hoja.empty:
        return False, ESTRUCTURA_NO_VALIDA, _detalle_generico_estructura()

    # Mapear nombres normalizados -> nombre original
    norm_to_orig = {}
    for c in hoja.columns:
        n = _normalizar_nombre_columna(c)
        norm_to_orig[n] = c

    presentes = set(norm_to_orig.keys())

    # Todas las columnas del archivo deben ser conocidas
    campos_permitidos = _CAMPOS_NUMERICOS | _CAMPOS_OPCIONALES
    desconocidos = presentes - campos_permitidos
    if desconocidos:
        return False, ESTRUCTURA_NO_VALIDA, _detalle_columnas_desconocidas(desconocidos)

    # Debe existir al menos un campo de cada grupo de movimiento
    if not (presentes & _CAMPOS_MOV_DEBITO):
        return False, ESTRUCTURA_NO_VALIDA, _detalle_falta_columna(
            "Débitos o Debe", list(_CAMPOS_MOV_DEBITO)
        )
    if not (presentes & _CAMPOS_MOV_CREDITO):
        return False, ESTRUCTURA_NO_VALIDA, _detalle_falta_columna(
            "Créditos o Haber", list(_CAMPOS_MOV_CREDITO)
        )

    # Deben estar todos los otros campos obligatorios
    faltantes = _CAMPOS_OTROS_OBLIGATORIOS - presentes
    if faltantes:
        return False, ESTRUCTURA_NO_VALIDA, _detalle_faltan_obligatorios(faltantes)

    # Al menos 8 columnas físicas (8 lógicas obligatorias) y como máximo todas las permitidas
    if not (8 <= len(hoja.columns) <= len(campos_permitidos)):
        return False, ESTRUCTURA_NO_VALIDA, _detalle_cantidad_columnas()

    # Columnas numéricas: solo valores numéricos (vacío = 0)
    for col_norm in _CAMPOS_NUMERICOS & presentes:
        col_orig = norm_to_orig[col_norm]
        serie = hoja[col_orig]
        numeros = pd.to_numeric(serie, errors="coerce")
        if (numeros.isna() & serie.notna()).any():
            return False, ESTRUCTURA_NO_VALIDA, _detalle_valores_no_numericos()

    # Cuadratura: sum(Débitos) = sum(Créditos), aceptando Debe/Haber como sinónimos
    col_debitos_norm = next(iter((presentes & _CAMPOS_MOV_DEBITO)))
    col_creditos_norm = next(iter((presentes & _CAMPOS_MOV_CREDITO)))
    col_debitos = norm_to_orig[col_debitos_norm]
    col_creditos = norm_to_orig[col_creditos_norm]
    suma_debitos = pd.to_numeric(hoja[col_debitos], errors="coerce").fillna(0).sum()
    suma_creditos = pd.to_numeric(hoja[col_creditos], errors="coerce").fillna(0).sum()
    if suma_debitos != suma_creditos:
        return False, ESTRUCTURA_NO_VALIDA, _detalle_suma_debe_haber(suma_debitos, suma_creditos)

    return True, ESTRUCTURA_VALIDA, None

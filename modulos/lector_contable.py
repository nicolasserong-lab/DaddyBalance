import pandas as pd # Importamos pandas para procesar tablas

def procesar_balance_8_columnas(ruta_archivo):
    """
    Esta función lee un archivo Excel de balance y limpia los datos.
    """
    try:
        # Leemos el archivo Excel
        # Usamos engine='openpyxl' para archivos .xlsx modernos
        datos = pd.read_excel(ruta_archivo, engine='openpyxl')
        
        # Aquí eliminamos filas que estén completamente vacías
        datos_limpios = datos.dropna(how='all')
        
        # Retornamos el dataframe (la tabla) para que el programa principal la use
        return datos_limpios
    
    except Exception as e:
        # Si algo sale mal, devolvemos el error para mostrarlo en pantalla
        return f"Error al leer el archivo: {str(e)}"

def detectar_gastos_rechazados(df):
    """
    Busca palabras clave en las cuentas contables que sugieran gastos rechazados.
    """
    # Lista de palabras sospechosas (puedes pedirle más a tu papá luego)
    palabras_clave = ['MULTA', 'INTERES', 'RETIRO', 'SANCION', 'GASTO PERSONAL']
    
    # EXPLICACIÓN DEL CAMBIO:
    # 1. df.iloc[:, 1] selecciona la segunda columna (Cuentas)
    # 2. .astype(str) asegura que todo sea texto
    # 3. .str.upper() lo pasa a MAYÚSCULAS
    # 4. .str.contains() busca las palabras (aquí faltaba el .str)
    
    columna_cuentas = df.iloc[:, 1].astype(str).str.upper()
    filtro = columna_cuentas.str.contains('|'.join(palabras_clave), na=False)
    
    # Retornamos las filas que cumplen con la búsqueda
    return df[filtro]
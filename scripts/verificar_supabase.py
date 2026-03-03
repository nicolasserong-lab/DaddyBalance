"""
Sprint A: Verificar conexión a Supabase y que la tabla actividad exista.
Ejecutar desde la raíz del proyecto.

  python scripts/verificar_supabase.py

Lee SUPABASE_URL y SUPABASE_KEY de:
  1) Variables de entorno SUPABASE_URL y SUPABASE_KEY, o
  2) .streamlit/secrets.toml (si existe)
"""
import os
import sys

def _cargar_secrets():
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_KEY", "").strip()
    if url and key:
        return url, key
    # Buscar .streamlit/secrets.toml desde la raíz del proyecto (cwd al ejecutar desde DaddyBalance)
    raiz = os.getcwd()
    secrets_path = os.path.join(raiz, ".streamlit", "secrets.toml")
    if not os.path.isfile(secrets_path):
        # Fallback: ruta relativa al script (subir un nivel desde scripts/)
        raiz_script = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        secrets_path = os.path.join(raiz_script, ".streamlit", "secrets.toml")
    if os.path.isfile(secrets_path):
        try:
            import tomli
            with open(secrets_path, "rb") as f:
                s = tomli.load(f)
            url = str(s.get("SUPABASE_URL") or "").strip()
            key = str(s.get("SUPABASE_KEY") or "").strip()
            if url and key:
                return url, key
        except Exception as e:
            print("(Al leer secrets.toml:", e, ")")
    return "", ""

def main():
    url, key = _cargar_secrets()

    if not url or not key:
        print("Falta SUPABASE_URL o SUPABASE_KEY.")
        print("Ponelas en .streamlit/secrets.toml o como variables de entorno.")
        print("Asegurate de ejecutar desde la raíz del proyecto: cd C:\\Users\\nicol\\Desktop\\DaddyBalance")
        print("Ejemplo en PowerShell: $env:SUPABASE_URL=\"https://...\"; $env:SUPABASE_KEY=\"sb_publishable_...\"")
        sys.exit(1)

    try:
        from supabase import create_client
    except ImportError:
        print("Instalá dependencias: pip install -r requirements.txt")
        sys.exit(1)

    try:
        client = create_client(url, key)
        r = client.table("actividad").select("*").limit(1).execute()
        print("OK. Conexión a Supabase correcta.")
        print("Tabla 'actividad' existe. Filas devueltas:", len(r.data))
        if r.data:
            print("Ejemplo:", r.data[0])
        else:
            print("(La tabla está vacía; es normal hasta que uses Cargar Balance o Análisis de Renta.)")
    except Exception as e:
        print("Error:", e)
        sys.exit(1)

if __name__ == "__main__":
    main()

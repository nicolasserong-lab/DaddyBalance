# DaddyBalance

Aplicación web para **análisis contable y fiscal** en formato balance de 8 columnas (plan chileno): carga de Excel, validaciones, cálculo de Renta Líquida Imponible (RLI) e impuesto (régimen D3/D8), consultor con IA (Groq) e historial en línea con Supabase.

---

## Requisitos

- **Python 3.9+** (recomendado 3.10 o 3.11)
- Dependencias en `requirements.txt`

---

## Ejecución en local

1. **Clonar el repositorio** (o abrir la carpeta del proyecto).

2. **Crear y activar el entorno virtual** (recomendado):
   ```bash
   python -m venv entorno_DaddyBalance
   # Windows (PowerShell):
   .\entorno_DaddyBalance\Scripts\activate
   # Windows (CMD):
   entorno_DaddyBalance\Scripts\activate.bat
   ```

3. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar secretos** en `.streamlit/secrets.toml` (crear el archivo si no existe). No subas este archivo a Git. Claves necesarias:

   | Clave | Descripción | Dónde obtenerla |
   |-------|-------------|----------------|
   | `APP_PASSWORD` | Contraseña de acceso a la app | La que elijas |
   | `GROQ_API_KEY` | API Key de Groq para el Consultor IA | [console.groq.com](https://console.groq.com) |
   | `SUPABASE_URL` | URL del proyecto Supabase | Supabase → Project Settings → API |
   | `SUPABASE_KEY` | Publishable key (clave pública) | Supabase → Settings → API Keys |

   Ejemplo de contenido mínimo de `secrets.toml`:
   ```toml
   APP_PASSWORD = "tu_contraseña"
   GROQ_API_KEY = "tu_api_key_groq"
   SUPABASE_URL = "https://xxxx.supabase.co"
   SUPABASE_KEY = "sb_publishable_..."
   ```

5. **Ejecutar la aplicación:**
   ```bash
   streamlit run Principal.py
   ```
   Abrí en el navegador la URL que muestre la terminal (por defecto `http://localhost:8501`).

---

## Verificar conexión a Supabase

Para comprobar que Supabase está bien configurado y la tabla existe:

```bash
python scripts/verificar_supabase.py
```

Debe mostrar: `OK. Conexión a Supabase correcta. Tabla 'actividad' existe.`

---

## Despliegue en Streamlit Community Cloud (para usar por URL)

Así podés darle a tu papá (o a quien quieras) un enlace para usar la app en línea.

### 1. Subir el código a GitHub

- Crea un repositorio en GitHub y sube el proyecto.
- **No subas** el archivo `.streamlit/secrets.toml` (ya está en `.gitignore`).

### 2. Crear el proyecto en Supabase (si aún no lo tenés)

1. Entrá a [supabase.com](https://supabase.com) y creá un proyecto (plan gratuito).
2. En **SQL Editor** → New query, copiá y ejecutá el contenido del archivo `documentos/supabase_sprint_a_create_table.sql`. Eso crea la tabla `actividad`.
3. En **Project Settings → API** (o **Settings → API Keys**): copiá la **Project URL** y la **Publishable key** (no uses la secret key en la app).

### 3. Desplegar en Streamlit Cloud

1. Entrá a [share.streamlit.io](https://share.streamlit.io).
2. Iniciá sesión con GitHub y elegí **New app**.
3. Seleccioná el repositorio **DaddyBalance**, branch (por ejemplo `main`) y como archivo principal **`Principal.py`**.
4. En **Advanced settings** → **Secrets**, pegá el contenido de tu `secrets.toml` **de producción** (mismas claves que en la tabla de más arriba). Ejemplo:
   ```toml
   APP_PASSWORD = "contraseña_para_produccion"
   GROQ_API_KEY = "tu_api_key_groq"
   SUPABASE_URL = "https://tu-proyecto.supabase.co"
   SUPABASE_KEY = "sb_publishable_..."
   ```
5. Deploy. Cuando termine, Streamlit Cloud te dará una URL pública (por ejemplo `https://daddybalance.streamlit.app`).

### 4. Compartir la URL

Enviá esa URL a tu papá (o a quien vaya a usar la app). Solo tendrán que abrir el enlace, escribir la contraseña que definiste en `APP_PASSWORD` y usar la aplicación. Los datos de historial se guardan en tu proyecto de Supabase.

---

## Estructura del proyecto

- **Principal.py** — Punto de entrada, navegación (Inicio, Cargar Balance, Análisis de Renta, Ver historial) y lógica de pantallas.
- **modulos/** — Lógica de negocio: `lector_contable`, `calculos_renta`, `validaciones_carga`, `helpers_grilla`, `asistente_ia`, `config_renta`, `db`.
- **documentos/** — Script SQL para Supabase, carpeta de balances guardados, etc.
- **pruebas/** — Tests con pytest.
- **scripts/** — Script de verificación de Supabase.

---

## Pruebas

```bash
pytest pruebas/ -v
```

---

## Licencia

Uso según lo acordado en el repositorio.

"""Configuracion central: rutas, catalogos y conexion a la base de datos."""

import os
from pathlib import Path

from dotenv import load_dotenv

# --------------------------------------------------------------------------
# Rutas del proyecto
# --------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parent.parent

CSV_ORIGEN = RAIZ / "data" / "raw" / "Venta_online_c.csv"
CSV_LIMPIO = RAIZ / "data" / "processed" / "ventas_limpias.csv"
REPORTE_PERFILADO = RAIZ / "docs" / "perfilado.md"

# Delimitador ';' y fecha DD.MM.YY: pandas no los infiere por defecto.
CSV_SEPARADOR = ";"
FORMATO_FECHA = "%d.%m.%y"

# --------------------------------------------------------------------------
# Catalogos (segun la seccion 3.1 del enunciado)
# --------------------------------------------------------------------------

GENERO = {
    0: "Masculino",
    1: "Femenino",
}

METODO_PAGO = {
    0: "Efectivo",
    1: "Tarjeta de Credito",
    2: "Tarjeta de Debito",
}

NAVEGADOR = {
    0: "Tienda Fisica",
    1: "Navegador 1",
    2: "Navegador 2",
    3: "Navegador 3",
    4: "Navegador 4",
}

SI_NO = {
    0: "No",
    1: "Si",
}

# --------------------------------------------------------------------------
# Reglas de validacion de dominio
# --------------------------------------------------------------------------

# Rangos validos, para detectar valores imposibles (no outliers legitimos).
EDAD_MIN, EDAD_MAX = 18, 100
ANIO_ESPERADO = 2021

# Valores permitidos por columna categorica.
DOMINIOS = {
    "genero": set(GENERO),
    "metodo_pago_id": set(METODO_PAGO),
    "navegador_id": set(NAVEGADOR),
    "boletin": set(SI_NO),
    "vale": set(SI_NO),
}

# --------------------------------------------------------------------------
# Conexion a la base de datos
# --------------------------------------------------------------------------

load_dotenv(RAIZ / ".env")


def obtener_url_bd() -> str:
    """Devuelve la cadena de conexion a Postgres leida desde .env, tal cual."""
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "Falta DATABASE_URL. Copia .env.example como .env y coloca la "
            "cadena de conexion de Supabase."
        )
    return url


def obtener_url_sqlalchemy() -> str:
    """URL de conexion con el driver psycopg3 explicito, para SQLAlchemy."""
    url = obtener_url_bd()
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url

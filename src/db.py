"""Capa de acceso a la base de datos (puntos 2 a 5 del alcance).

Cada funcion resuelve un punto especifico del enunciado (indicado en su
comentario, ej. "Punto 3a"). Devuelven pandas.DataFrame, o un dict para
resultados de un solo valor (correlaciones). Serializables a JSON con
``df.to_dict(orient="records")``.

Prueba rapida contra la base de datos real:
    python src/db.py
"""

import pandas as pd
from scipy import stats
from sqlalchemy import Engine, create_engine, text

import config

_engine: Engine | None = None


# ---------------------------------------------------------------------------
# Conexion
# ---------------------------------------------------------------------------

def obtener_engine() -> Engine:
    """Crea (una sola vez) y reutiliza el engine de SQLAlchemy."""
    global _engine
    if _engine is None:
        _engine = create_engine(config.obtener_url_sqlalchemy(), pool_pre_ping=True)
    return _engine


def _consultar(sql: str) -> pd.DataFrame:
    """Ejecuta una consulta SQL y devuelve el resultado como DataFrame."""
    with obtener_engine().connect() as con:
        return pd.read_sql(text(sql), con)


# ---------------------------------------------------------------------------
# Punto 2a - Obtener los datos de la base de datos
# ---------------------------------------------------------------------------

def cargar_ventas() -> pd.DataFrame:
    """Extrae el dataset completo desde la vista v_ventas (1 fila por compra)."""
    return _consultar("SELECT * FROM v_ventas ORDER BY fecha_compra, id_cliente")


# ---------------------------------------------------------------------------
# Punto 2b - Estadisticas basicas (media, mediana, moda)
# ---------------------------------------------------------------------------

def estadisticas_basicas() -> pd.DataFrame:
    """Media, mediana, moda, desviacion y rango de las variables numericas.

    edad/venta_total/n_compras a nivel cliente; monto_compra/tiempo_seg a
    nivel compra, para no duplicar datos del cliente si llega a tener mas
    de una compra registrada.
    """
    sql = """
        SELECT 'edad' AS variable, round(avg(edad)::numeric, 2) AS media,
               percentile_cont(0.5) WITHIN GROUP (ORDER BY edad) AS mediana,
               mode() WITHIN GROUP (ORDER BY edad) AS moda,
               round(stddev(edad)::numeric, 2) AS desviacion,
               min(edad) AS minimo, max(edad) AS maximo
        FROM cliente
        UNION ALL
        SELECT 'venta_total', round(avg(venta_total), 2),
               percentile_cont(0.5) WITHIN GROUP (ORDER BY venta_total),
               mode() WITHIN GROUP (ORDER BY venta_total),
               round(stddev(venta_total), 2), min(venta_total), max(venta_total)
        FROM cliente
        UNION ALL
        SELECT 'n_compras', round(avg(n_compras)::numeric, 2),
               percentile_cont(0.5) WITHIN GROUP (ORDER BY n_compras),
               mode() WITHIN GROUP (ORDER BY n_compras),
               round(stddev(n_compras)::numeric, 2), min(n_compras), max(n_compras)
        FROM cliente
        UNION ALL
        SELECT 'monto_compra', round(avg(monto_compra), 2),
               percentile_cont(0.5) WITHIN GROUP (ORDER BY monto_compra),
               mode() WITHIN GROUP (ORDER BY monto_compra),
               round(stddev(monto_compra), 2), min(monto_compra), max(monto_compra)
        FROM compra
        UNION ALL
        SELECT 'tiempo_seg', round(avg(tiempo_seg)::numeric, 2),
               percentile_cont(0.5) WITHIN GROUP (ORDER BY tiempo_seg),
               mode() WITHIN GROUP (ORDER BY tiempo_seg),
               round(stddev(tiempo_seg)::numeric, 2), min(tiempo_seg), max(tiempo_seg)
        FROM compra
    """
    return _consultar(sql)


# ---------------------------------------------------------------------------
# Punto 2c - Distribucion de ventas por mes, metodo de pago, navegador,
# boletin y vale
# ---------------------------------------------------------------------------

def distribucion_mes() -> pd.DataFrame:
    """Cantidad de compras y monto total por mes."""
    sql = """
        SELECT mes, mes_nombre,
               count(*) AS compras,
               round(sum(monto_compra), 2) AS monto_total
        FROM v_ventas
        GROUP BY mes, mes_nombre
        ORDER BY mes
    """
    return _consultar(sql)


def distribucion_metodo_pago() -> pd.DataFrame:
    """Cantidad de compras y monto total por metodo de pago."""
    sql = """
        SELECT metodo_pago_desc AS metodo_pago,
               count(*) AS compras,
               round(sum(monto_compra), 2) AS monto_total,
               round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS porcentaje
        FROM v_ventas
        GROUP BY metodo_pago_desc
        ORDER BY compras DESC
    """
    return _consultar(sql)


def distribucion_navegador() -> pd.DataFrame:
    """Cantidad de compras y monto total por canal (navegador)."""
    sql = """
        SELECT navegador_desc AS navegador,
               count(*) AS compras,
               round(sum(monto_compra), 2) AS monto_total,
               round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS porcentaje
        FROM v_ventas
        GROUP BY navegador_desc
        ORDER BY compras DESC
    """
    return _consultar(sql)


def distribucion_boletin() -> pd.DataFrame:
    """Cantidad de clientes suscritos al boletin, a nivel cliente."""
    sql = """
        SELECT CASE boletin WHEN 1 THEN 'Si' ELSE 'No' END AS boletin,
               count(*) AS clientes,
               round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS porcentaje
        FROM cliente
        GROUP BY boletin
        ORDER BY boletin DESC
    """
    return _consultar(sql)


def distribucion_vale() -> pd.DataFrame:
    """Cantidad de clientes que utilizaron vale, a nivel cliente."""
    sql = """
        SELECT CASE vale WHEN 1 THEN 'Si' ELSE 'No' END AS vale,
               count(*) AS clientes,
               round(100.0 * count(*) / sum(count(*)) OVER (), 2) AS porcentaje
        FROM cliente
        GROUP BY vale
        ORDER BY vale DESC
    """
    return _consultar(sql)


# ---------------------------------------------------------------------------
# Punto 3a - Meses con mayores y menores ventas
# ---------------------------------------------------------------------------

def ventas_por_mes() -> pd.DataFrame:
    """Monto total, compras y ticket promedio por mes."""
    sql = """
        SELECT mes, mes_nombre,
               count(*) AS compras,
               round(sum(monto_compra), 2) AS monto_total,
               round(avg(monto_compra), 2) AS ticket_promedio
        FROM v_ventas
        GROUP BY mes, mes_nombre
        ORDER BY mes
    """
    return _consultar(sql)


def meses_extremos() -> dict:
    """Mes de mayor y menor venta total, derivados de ventas_por_mes()."""
    df = ventas_por_mes()
    top = df.loc[df["monto_total"].idxmax()]
    bajo = df.loc[df["monto_total"].idxmin()]
    return {
        "mes_mayor_venta": top["mes_nombre"],
        "monto_mayor_venta": float(top["monto_total"]),
        "mes_menor_venta": bajo["mes_nombre"],
        "monto_menor_venta": float(bajo["monto_total"]),
    }


# ---------------------------------------------------------------------------
# Punto 3b - Navegador mas preferido y menos popular
# ---------------------------------------------------------------------------

def popularidad_navegador() -> pd.DataFrame:
    """Alias semantico de distribucion_navegador() para el punto 3b."""
    return distribucion_navegador()


def navegadores_extremos() -> dict:
    """Navegador mas y menos usado, derivados de popularidad_navegador()."""
    df = popularidad_navegador()
    top = df.loc[df["compras"].idxmax()]
    bajo = df.loc[df["compras"].idxmin()]
    return {
        "navegador_mas_usado": top["navegador"],
        "compras_navegador_mas_usado": int(top["compras"]),
        "navegador_menos_usado": bajo["navegador"],
        "compras_navegador_menos_usado": int(bajo["compras"]),
    }


# ---------------------------------------------------------------------------
# Punto 3c - Ventas pagadas en efectivo vs. otros metodos
# ---------------------------------------------------------------------------

def ventas_por_metodo_pago() -> pd.DataFrame:
    """Desglose de ventas por metodo de pago, con la bandera es_efectivo.

    "Contra entrega" y "efectivo" corresponden al mismo metodo_pago_id = 0
    en el dataset; se interpreta como el total de Efectivo frente al resto.
    """
    sql = """
        SELECT metodo_pago_desc AS metodo_pago, es_efectivo,
               count(*) AS compras,
               round(sum(monto_compra), 2) AS monto_total
        FROM v_ventas
        GROUP BY metodo_pago_desc, es_efectivo
        ORDER BY monto_total DESC
    """
    return _consultar(sql)


def total_efectivo_vs_otros() -> pd.DataFrame:
    """Total pagado en efectivo vs. con tarjeta (credito + debito)."""
    sql = """
        SELECT CASE WHEN es_efectivo THEN 'Efectivo (contra entrega)'
                    ELSE 'Tarjeta (credito o debito)' END AS grupo,
               count(*) AS compras,
               round(sum(monto_compra), 2) AS monto_total,
               round(100.0 * sum(monto_compra) / sum(sum(monto_compra)) OVER (), 2) AS porcentaje
        FROM v_ventas
        GROUP BY es_efectivo
        ORDER BY monto_total DESC
    """
    return _consultar(sql)


# ---------------------------------------------------------------------------
# Punto 3d - Meses donde se usaron mas boletines y vales
# ---------------------------------------------------------------------------

def boletin_vale_por_mes() -> pd.DataFrame:
    """Compras por mes de clientes suscritos a boletin y de clientes con vale."""
    sql = """
        SELECT mes, mes_nombre,
               count(*) FILTER (WHERE boletin = 1) AS compras_con_boletin,
               count(*) FILTER (WHERE vale = 1)    AS compras_con_vale
        FROM v_ventas
        GROUP BY mes, mes_nombre
        ORDER BY mes
    """
    return _consultar(sql)


def meses_maximos_boletin_vale() -> dict:
    """Meses con mayor cantidad de compras asociadas a boletin y vale."""
    datos = boletin_vale_por_mes()

    fila_boletin = datos.loc[datos["compras_con_boletin"].idxmax()]
    fila_vale = datos.loc[datos["compras_con_vale"].idxmax()]

    return {
        "mes_mayor_boletin": str(fila_boletin["mes_nombre"]),
        "compras_con_boletin": int(fila_boletin["compras_con_boletin"]),
        "mes_mayor_vale": str(fila_vale["mes_nombre"]),
        "compras_con_vale": int(fila_vale["compras_con_vale"]),
    }


# ---------------------------------------------------------------------------
# Punto 4a - Segmentacion de clientes por edad
# ---------------------------------------------------------------------------

def segmentacion_edad() -> pd.DataFrame:
    """Patrones de compra agrupados en 6 rangos de edad de 10 anios."""
    sql = """
        SELECT rango_edad,
               count(*) AS clientes,
               round(avg(venta_total), 2) AS venta_promedio,
               round(avg(n_compras), 2) AS compras_promedio,
               round(sum(venta_total), 2) AS venta_total_segmento
        FROM (
            SELECT
                CASE
                    WHEN edad BETWEEN 18 AND 27 THEN '18-27'
                    WHEN edad BETWEEN 28 AND 37 THEN '28-37'
                    WHEN edad BETWEEN 38 AND 47 THEN '38-47'
                    WHEN edad BETWEEN 48 AND 57 THEN '48-57'
                    WHEN edad BETWEEN 58 AND 67 THEN '58-67'
                    ELSE '68+'
                END AS rango_edad,
                CASE
                    WHEN edad BETWEEN 18 AND 27 THEN 1
                    WHEN edad BETWEEN 28 AND 37 THEN 2
                    WHEN edad BETWEEN 38 AND 47 THEN 3
                    WHEN edad BETWEEN 48 AND 57 THEN 4
                    WHEN edad BETWEEN 58 AND 67 THEN 5
                    ELSE 6
                END AS orden,
                venta_total, n_compras
            FROM cliente
        ) t
        GROUP BY rango_edad, orden
        ORDER BY orden
    """
    return _consultar(sql)


# ---------------------------------------------------------------------------
# Punto 4b - Comparacion de comportamiento de compra entre generos
# ---------------------------------------------------------------------------

def comparacion_genero() -> pd.DataFrame:
    """Patrones de compra agrupados por genero."""
    sql = """
        SELECT CASE genero WHEN 1 THEN 'Femenino' ELSE 'Masculino' END AS genero,
               count(*) AS clientes,
               round(avg(edad), 1) AS edad_promedio,
               round(avg(venta_total), 2) AS venta_promedio,
               round(avg(n_compras), 2) AS compras_promedio,
               round(sum(venta_total), 2) AS venta_total_segmento
        FROM cliente
        GROUP BY genero
    """
    return _consultar(sql)


# ---------------------------------------------------------------------------
# Punto 4c - Segmentacion por boletin y vale
# ---------------------------------------------------------------------------

def segmentacion_boletin_vale() -> pd.DataFrame:
    """Patrones de compra por combinacion de boletin y vale."""
    sql = """
        SELECT CASE boletin WHEN 1 THEN 'Si' ELSE 'No' END AS boletin,
               CASE vale    WHEN 1 THEN 'Si' ELSE 'No' END AS vale,
               count(*) AS clientes,
               round(avg(venta_total), 2) AS venta_promedio,
               round(avg(n_compras), 2) AS compras_promedio
        FROM cliente
        GROUP BY boletin, vale
        ORDER BY boletin DESC, vale DESC
    """
    return _consultar(sql)


# ---------------------------------------------------------------------------
# Punto 5 - Correlaciones
# ---------------------------------------------------------------------------

def _cramers_v(tabla: pd.DataFrame) -> dict:
    """Chi-cuadrado y V de Cramer (0 a 1) para una tabla de contingencia."""
    chi2, p_valor, gl, _ = stats.chi2_contingency(tabla)
    n = tabla.to_numpy().sum()
    filas, columnas = tabla.shape
    v = (chi2 / (n * (min(filas, columnas) - 1))) ** 0.5
    return {
        "chi2": round(float(chi2), 4),
        "p_valor": round(float(p_valor), 6),
        "grados_libertad": int(gl),
        "cramers_v": round(float(v), 4),
        "significativo_95": bool(p_valor < 0.05),
        "tabla_contingencia": tabla.to_dict(),
    }


def correlacion_venta_edad() -> dict:
    """Punto 5a: correlacion de Pearson entre venta_total y edad (por cliente)."""
    df = _consultar("SELECT edad, venta_total FROM cliente")
    r, p_valor = stats.pearsonr(df["edad"], df["venta_total"])
    return {
        "variable_x": "edad",
        "variable_y": "venta_total",
        "pearson_r": round(float(r), 4),
        "p_valor": round(float(p_valor), 6),
        "significativo_95": bool(p_valor < 0.05),
        "n": len(df),
    }


def correlacion_genero_metodo_pago() -> dict:
    """Punto 5b: asociacion entre genero y metodo de pago preferido."""
    df = _consultar(
        "SELECT genero_desc, metodo_pago_desc FROM v_ventas"
    )
    tabla = pd.crosstab(df["genero_desc"], df["metodo_pago_desc"])
    return _cramers_v(tabla)


def correlacion_boletin_vale() -> dict:
    """Punto 5c: asociacion entre uso de boletin y uso de vale."""
    df = _consultar("SELECT boletin, vale FROM cliente")
    tabla = pd.crosstab(df["boletin"], df["vale"])
    return _cramers_v(tabla)


# ---------------------------------------------------------------------------
# Prueba rapida contra la base de datos real
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    funciones_tabla = [
        ("2a  cargar_ventas", cargar_ventas),
        ("2b  estadisticas_basicas", estadisticas_basicas),
        ("2c  distribucion_mes", distribucion_mes),
        ("2c  distribucion_metodo_pago", distribucion_metodo_pago),
        ("2c  distribucion_navegador", distribucion_navegador),
        ("2c  distribucion_boletin", distribucion_boletin),
        ("2c  distribucion_vale", distribucion_vale),
        ("3a  ventas_por_mes", ventas_por_mes),
        ("3b  popularidad_navegador", popularidad_navegador),
        ("3c  ventas_por_metodo_pago", ventas_por_metodo_pago),
        ("3c  total_efectivo_vs_otros", total_efectivo_vs_otros),
        ("3d  boletin_vale_por_mes", boletin_vale_por_mes),
        ("4a  segmentacion_edad", segmentacion_edad),
        ("4b  comparacion_genero", comparacion_genero),
        ("4c  segmentacion_boletin_vale", segmentacion_boletin_vale),
    ]

    print("Prueba de la capa de acceso (src/db.py)")
    print("=" * 60)
    for etiqueta, fn in funciones_tabla:
        df = fn()
        print(f"{etiqueta:35s} -> {len(df):5d} filas x {len(df.columns)} columnas")

    print("-" * 60)
    for etiqueta, fn in [
        ("3a  meses_extremos", meses_extremos),
        ("3b  navegadores_extremos", navegadores_extremos),
        ("3d  meses_maximos_boletin_vale", meses_maximos_boletin_vale),
        ("5a  correlacion_venta_edad", correlacion_venta_edad),
        ("5b  correlacion_genero_metodo_pago", correlacion_genero_metodo_pago),
        ("5c  correlacion_boletin_vale", correlacion_boletin_vale),
    ]:
        print(f"{etiqueta}: {fn()}")

    print("=" * 60)
    print("OK - todas las funciones respondieron correctamente")

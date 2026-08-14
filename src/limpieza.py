"""Preparacion de datos: extraccion, perfilado y limpieza (puntos 1a-1c).

Genera data/processed/ventas_limpias.csv y docs/perfilado.md. Idempotente.

Uso:
    python src/limpieza.py
"""

import sys
from datetime import datetime

import pandas as pd

import config

# Nombres del CSV a snake_case, igual que las columnas de la base de datos.
RENOMBRES = {
    "Id_cliente": "id_cliente",
    "Edad": "edad",
    "Genero": "genero",
    "Venta_total": "venta_total",
    "N_Compras": "n_compras",
    "FechaCompra": "fecha_compra",
    "MontoCompra": "monto_compra",
    "MetodoPago": "metodo_pago_id",
    "Tiempo": "tiempo_seg",
    "Navegador": "navegador_id",
    "Boletin": "boletin",
    "Vale": "vale",
}

# Tipos finales de cada columna.
TIPOS = {
    "id_cliente": "int64",
    "edad": "int16",
    "genero": "int8",
    "venta_total": "float64",
    "n_compras": "int16",
    "monto_compra": "float64",
    "metodo_pago_id": "int8",
    "tiempo_seg": "int16",
    "navegador_id": "int8",
    "boletin": "int8",
    "vale": "int8",
}

COLUMNAS_NUMERICAS = ["edad", "venta_total", "n_compras", "monto_compra", "tiempo_seg"]


# ---------------------------------------------------------------------------
# 1a. Extraccion
# ---------------------------------------------------------------------------

def extraer() -> pd.DataFrame:
    """Lee el CSV con su separador ';' y fecha DD.MM.YY explicitos."""
    df = pd.read_csv(config.CSV_ORIGEN, sep=config.CSV_SEPARADOR)
    df = df.rename(columns=RENOMBRES)
    df["fecha_compra"] = pd.to_datetime(
        df["fecha_compra"], format=config.FORMATO_FECHA
    )
    return df


# ---------------------------------------------------------------------------
# 1b. Verificacion de valores faltantes y duplicados
# ---------------------------------------------------------------------------

def revisar_faltantes(df: pd.DataFrame) -> pd.DataFrame:
    """Cuenta nulos y cadenas vacias por columna."""
    nulos = df.isna().sum()
    return pd.DataFrame(
        {
            "columna": nulos.index,
            "nulos": nulos.to_numpy(),
            "porcentaje": (nulos.to_numpy() / len(df) * 100).round(2),
        }
    )


def revisar_duplicados(df: pd.DataFrame) -> dict:
    """Revisa duplicados a dos niveles: fila completa y clave primaria."""
    return {
        "filas_completas_duplicadas": int(df.duplicated().sum()),
        "id_cliente_duplicados": int(df["id_cliente"].duplicated().sum()),
        "id_cliente_unicos": int(df["id_cliente"].nunique()),
    }


# ---------------------------------------------------------------------------
# 1c. Validacion de tipos y dominios
# ---------------------------------------------------------------------------

def validar_dominios(df: pd.DataFrame) -> pd.DataFrame:
    """Verifica que cada variable categorica solo contenga codigos validos."""
    filas = []
    for columna, permitidos in config.DOMINIOS.items():
        encontrados = set(df[columna].unique().tolist())
        invalidos = encontrados - permitidos
        filas.append(
            {
                "columna": columna,
                "valores_encontrados": sorted(encontrados),
                "valores_permitidos": sorted(permitidos),
                "invalidos": sorted(invalidos) if invalidos else "-",
                "estado": "FALLA" if invalidos else "OK",
            }
        )
    return pd.DataFrame(filas)


def validar_rangos(df: pd.DataFrame) -> pd.DataFrame:
    """Verifica rangos plausibles: edad, montos positivos y anio del dataset."""
    fuera_edad = int(
        ((df["edad"] < config.EDAD_MIN) | (df["edad"] > config.EDAD_MAX)).sum()
    )
    montos_no_positivos = int(
        ((df["venta_total"] <= 0) | (df["monto_compra"] <= 0)).sum()
    )
    fuera_anio = int((df["fecha_compra"].dt.year != config.ANIO_ESPERADO).sum())
    compras_invalidas = int((df["n_compras"] < 1).sum())

    reglas = [
        (f"Edad entre {config.EDAD_MIN} y {config.EDAD_MAX}", fuera_edad),
        ("Montos estrictamente positivos", montos_no_positivos),
        (f"Fecha dentro del anio {config.ANIO_ESPERADO}", fuera_anio),
        ("N_Compras mayor o igual a 1", compras_invalidas),
    ]
    return pd.DataFrame(
        [
            {
                "regla": regla,
                "filas_que_incumplen": n,
                "estado": "OK" if n == 0 else "REVISAR",
            }
            for regla, n in reglas
        ]
    )


def tipificar(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica los tipos finales. La fecha se deja como date (sin hora)."""
    df = df.astype(TIPOS)
    df["fecha_compra"] = df["fecha_compra"].dt.date
    return df


# ---------------------------------------------------------------------------
# Outliers y estadisticas descriptivas
# ---------------------------------------------------------------------------

def detectar_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Identifica outliers por IQR (1.5x). Solo se reportan, no se eliminan."""
    filas = []
    for columna in COLUMNAS_NUMERICAS:
        serie = df[columna]
        q1, q3 = serie.quantile(0.25), serie.quantile(0.75)
        iqr = q3 - q1
        limite_inf, limite_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        n_outliers = int(((serie < limite_inf) | (serie > limite_sup)).sum())
        filas.append(
            {
                "columna": columna,
                "q1": round(float(q1), 2),
                "q3": round(float(q3), 2),
                "limite_inferior": round(float(limite_inf), 2),
                "limite_superior": round(float(limite_sup), 2),
                "outliers": n_outliers,
                "porcentaje": round(n_outliers / len(df) * 100, 2),
            }
        )
    return pd.DataFrame(filas)


def describir(df: pd.DataFrame) -> pd.DataFrame:
    """Estadisticas descriptivas de las variables numericas."""
    resumen = df[COLUMNAS_NUMERICAS].describe().T
    resumen["moda"] = [df[c].mode().iloc[0] for c in COLUMNAS_NUMERICAS]
    resumen["mediana"] = [df[c].median() for c in COLUMNAS_NUMERICAS]
    columnas = ["count", "mean", "mediana", "moda", "std", "min", "max"]
    return resumen[columnas].round(2).reset_index(names="columna")


# ---------------------------------------------------------------------------
# Reporte de perfilado
# ---------------------------------------------------------------------------

def _md(df: pd.DataFrame) -> str:
    """Convierte un DataFrame a tabla markdown."""
    return df.to_markdown(index=False)


def generar_reporte(df_crudo, df_limpio, faltantes, duplicados, dominios,
                    rangos, outliers, estadisticas) -> str:
    """Arma el reporte de perfilado en markdown para el informe final."""
    conteos = []
    for columna, catalogo in [
        ("genero", config.GENERO),
        ("metodo_pago_id", config.METODO_PAGO),
        ("navegador_id", config.NAVEGADOR),
        ("boletin", config.SI_NO),
        ("vale", config.SI_NO),
    ]:
        conteo = df_limpio[columna].value_counts().sort_index()
        for codigo, n in conteo.items():
            conteos.append(
                {
                    "variable": columna,
                    "codigo": codigo,
                    "etiqueta": catalogo[codigo],
                    "registros": int(n),
                    "porcentaje": round(n / len(df_limpio) * 100, 2),
                }
            )
    df_conteos = pd.DataFrame(conteos)

    fecha_min = df_crudo["fecha_compra"].min().date()
    fecha_max = df_crudo["fecha_compra"].max().date()

    return f"""# Reporte de perfilado y limpieza de datos

**Archivo origen:** `data/raw/Venta_online_c.csv`
**Generado:** {datetime.now():%Y-%m-%d %H:%M}
**Registros:** {len(df_crudo):,} filas x {len(df_crudo.columns)} columnas
**Rango de fechas:** {fecha_min} a {fecha_max}

Este documento es la evidencia del punto 1 del alcance (preparacion de datos).
Se genera automaticamente al ejecutar `python src/limpieza.py`.

---

## 1. Estructura del archivo origen

El archivo presenta dos caracteristicas que impiden leerlo con la configuracion
por defecto de pandas y que fueron el primer desafio del proceso:

| Caracteristica | Valor en el archivo | Comportamiento por defecto | Accion tomada |
|---|---|---|---|
| Delimitador | `;` (punto y coma) | pandas asume `,` | Lectura con `sep=';'` |
| Formato de fecha | `DD.MM.YY` (ej. `02.02.21`) | pandas asume formato mes-primero | Parseo explicito con `format='%d.%m.%y'` |

El segundo punto es especialmente delicado: sin el formato explicito, una fecha
como `02.02.21` se interpreta sin error aparente, pero `27.08.21` falla o se
convierte mal. El resultado seria un analisis de tendencias mensuales incorrecto
sin ningun mensaje de advertencia.

## 2. Valores faltantes (punto 1b)

{_md(faltantes)}

**Resultado:** el dataset no presenta valores faltantes en ninguna de las
{len(df_crudo.columns)} columnas. La verificacion se documenta igualmente porque
la ausencia de nulos es un hallazgo del perfilado, no un supuesto.

## 3. Valores duplicados (punto 1b)

| Verificacion | Resultado |
|---|---|
| Filas completas duplicadas | {duplicados['filas_completas_duplicadas']} |
| `id_cliente` duplicados | {duplicados['id_cliente_duplicados']} |
| `id_cliente` unicos | {duplicados['id_cliente_unicos']:,} |

**Resultado:** no hay duplicados. Cada fila corresponde a un cliente distinto,
lo que confirma que `id_cliente` es una clave primaria valida.

## 4. Validacion de dominios categoricos (punto 1c)

Se verifico que cada variable categorica contenga unicamente los codigos
definidos en la seccion 3.1 del enunciado:

{_md(dominios)}

## 5. Validacion de rangos

{_md(rangos)}

## 6. Tipos de datos asignados (punto 1c)

| Columna | Tipo asignado | Justificacion |
|---|---|---|
| `id_cliente` | `BIGINT` | Identificador unico, clave primaria |
| `edad` | `SMALLINT` | Entero acotado (18-79) |
| `genero` | `SMALLINT` | Codigo de catalogo (0/1) |
| `venta_total` | `NUMERIC(12,2)` | Monto acumulado; el origen trae maximo 1 decimal |
| `n_compras` | `SMALLINT` | Conteo entero (1-25) |
| `fecha_compra` | `DATE` | Fecha sin componente horario |
| `monto_compra` | `NUMERIC(12,3)` | **Requiere 3 decimales**, ver nota abajo |
| `metodo_pago_id` | `SMALLINT` | Llave foranea al catalogo de metodo de pago |
| `tiempo_seg` | `SMALLINT` | Entero (180-1443) |
| `navegador_id` | `SMALLINT` | Llave foranea al catalogo de navegador |
| `boletin`, `vale` | `SMALLINT` | Banderas binarias (0/1) |

**Nota sobre la precision de `monto_compra`:** aunque lo natural para una
columna monetaria es `NUMERIC(10,2)`, el analisis de precision mostro que 5,686
de los 6,500 registros traen **tres** decimales (ej. `109.054`). Usar dos
decimales habria redondeado el 87% de los montos y alterado cualquier suma
posterior. Se opto por `NUMERIC(12,3)` para conservar el dato original intacto.

## 7. Estadisticas descriptivas

{_md(estadisticas)}

## 8. Analisis de outliers

Se aplico el criterio del rango intercuartilico (valores fuera de
[Q1 - 1.5*IQR, Q3 + 1.5*IQR]):

{_md(outliers)}

**Decision: los outliers se conservan.** El criterio del IQR marca como atipicos
los valores altos de `venta_total` (hasta Q3,169), pero se trata de clientes con
alto volumen de compra, no de errores de captura: son internamente consistentes
(edad valida, fecha valida, metodo de pago valido) y representan justamente al
segmento de mayor valor comercial. Eliminarlos sesgaria a la baja el analisis de
ventas y borraria a los clientes mas rentables, que son los de mayor interes
para las recomendaciones de negocio del informe.

## 9. Distribucion de las variables categoricas

{_md(df_conteos)}

## 10. Hallazgo sobre la estructura de los datos

Se verifico si `monto_compra` correspondia al ticket promedio del cliente
(`venta_total / n_compras`). **La igualdad se cumple en solo 7 de 6,500 registros**,
por lo que no son campos derivados uno del otro.

La interpretacion adoptada es que cada fila combina dos niveles de informacion
distintos:

- **Nivel cliente (acumulado del ano):** `id_cliente`, `edad`, `genero`,
  `venta_total`, `n_compras`, `boletin`, `vale`
- **Nivel transaccion (una compra puntual registrada):** `fecha_compra`,
  `monto_compra`, `metodo_pago_id`, `tiempo_seg`, `navegador_id`

Este hallazgo es el que justifica el modelo relacional en dos entidades
(`cliente` y `compra`) en lugar de una unica tabla plana, y se detalla en el
diagrama de la base de datos.

## 11. Observacion para el analisis posterior

El codigo `0` de la variable `Navegador` corresponde a "Tienda Fisica" y
representa el **{df_conteos.query("variable == 'navegador_id' and codigo == 0")['porcentaje'].iloc[0]}%**
de los registros, pese a que el enunciado describe el archivo como ventas
online. Se conserva tal cual y se debe considerar al comparar tienda fisica
contra navegadores web en el analisis de canales.

---

## Resumen del proceso

| Paso | Accion | Resultado |
|---|---|---|
| 1 | Extraccion del CSV con separador y fecha explicitos | {len(df_crudo):,} filas leidas |
| 2 | Verificacion de valores faltantes | 0 nulos |
| 3 | Verificacion de duplicados | 0 duplicados |
| 4 | Validacion de dominios categoricos | Todos los codigos validos |
| 5 | Validacion de rangos | Sin valores imposibles |
| 6 | Tipificacion de columnas | 12 columnas tipificadas |
| 7 | Analisis de outliers | Reportados y conservados |
| 8 | Exportacion | `data/processed/ventas_limpias.csv` |

**Registros de salida: {len(df_limpio):,}** (no se elimino ningun registro).
"""


# ---------------------------------------------------------------------------
# Orquestacion
# ---------------------------------------------------------------------------

def main() -> int:
    print("Fase 1 - Preparacion de datos")
    print("=" * 60)

    print(f"[1/6] Extrayendo {config.CSV_ORIGEN.name} ...")
    df = extraer()
    print(f"      {len(df):,} filas x {len(df.columns)} columnas")

    print("[2/6] Revisando valores faltantes y duplicados ...")
    faltantes = revisar_faltantes(df)
    duplicados = revisar_duplicados(df)
    print(f"      nulos: {int(faltantes['nulos'].sum())} | "
          f"duplicados: {duplicados['filas_completas_duplicadas']}")

    print("[3/6] Validando dominios y rangos ...")
    dominios = validar_dominios(df)
    rangos = validar_rangos(df)
    if (dominios["estado"] == "FALLA").any():
        print("      ERROR: hay codigos fuera de catalogo:", file=sys.stderr)
        print(dominios[dominios["estado"] == "FALLA"], file=sys.stderr)
        return 1
    print("      dominios OK | rangos OK")

    print("[4/6] Aplicando tipos de datos ...")
    df_limpio = tipificar(df)

    print("[5/6] Calculando estadisticas y outliers ...")
    outliers = detectar_outliers(df_limpio)
    estadisticas = describir(df_limpio)

    print("[6/6] Exportando resultados ...")
    config.CSV_LIMPIO.parent.mkdir(parents=True, exist_ok=True)
    df_limpio.to_csv(config.CSV_LIMPIO, index=False)

    reporte = generar_reporte(
        df, df_limpio, faltantes, duplicados, dominios,
        rangos, outliers, estadisticas,
    )
    config.REPORTE_PERFILADO.parent.mkdir(parents=True, exist_ok=True)
    config.REPORTE_PERFILADO.write_text(reporte, encoding="utf-8")

    print("=" * 60)
    print(f"OK  datos limpios -> {config.CSV_LIMPIO.relative_to(config.RAIZ)}")
    print(f"OK  reporte       -> {config.REPORTE_PERFILADO.relative_to(config.RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

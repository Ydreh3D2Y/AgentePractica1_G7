# Reporte de perfilado y limpieza de datos

**Archivo origen:** `data/raw/Venta_online_c.csv`
**Generado:** 2026-08-13 22:19
**Registros:** 6,500 filas x 12 columnas
**Rango de fechas:** 2021-01-01 a 2021-12-31

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

| columna        |   nulos |   porcentaje |
|:---------------|--------:|-------------:|
| id_cliente     |       0 |            0 |
| edad           |       0 |            0 |
| genero         |       0 |            0 |
| venta_total    |       0 |            0 |
| n_compras      |       0 |            0 |
| fecha_compra   |       0 |            0 |
| monto_compra   |       0 |            0 |
| metodo_pago_id |       0 |            0 |
| tiempo_seg     |       0 |            0 |
| navegador_id   |       0 |            0 |
| boletin        |       0 |            0 |
| vale           |       0 |            0 |

**Resultado:** el dataset no presenta valores faltantes en ninguna de las
12 columnas. La verificacion se documenta igualmente porque
la ausencia de nulos es un hallazgo del perfilado, no un supuesto.

## 3. Valores duplicados (punto 1b)

| Verificacion | Resultado |
|---|---|
| Filas completas duplicadas | 0 |
| `id_cliente` duplicados | 0 |
| `id_cliente` unicos | 6,500 |

**Resultado:** no hay duplicados. Cada fila corresponde a un cliente distinto,
lo que confirma que `id_cliente` es una clave primaria valida.

## 4. Validacion de dominios categoricos (punto 1c)

Se verifico que cada variable categorica contenga unicamente los codigos
definidos en la seccion 3.1 del enunciado:

| columna        | valores_encontrados   | valores_permitidos   | invalidos   | estado   |
|:---------------|:----------------------|:---------------------|:------------|:---------|
| genero         | [0, 1]                | [0, 1]               | -           | OK       |
| metodo_pago_id | [0, 1, 2]             | [0, 1, 2]            | -           | OK       |
| navegador_id   | [0, 1, 2, 3, 4]       | [0, 1, 2, 3, 4]      | -           | OK       |
| boletin        | [0, 1]                | [0, 1]               | -           | OK       |
| vale           | [0, 1]                | [0, 1]               | -           | OK       |

## 5. Validacion de rangos

| regla                          |   filas_que_incumplen | estado   |
|:-------------------------------|----------------------:|:---------|
| Edad entre 18 y 100            |                     0 | OK       |
| Montos estrictamente positivos |                     0 | OK       |
| Fecha dentro del anio 2021     |                     0 | OK       |
| N_Compras mayor o igual a 1    |                     0 | OK       |

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

| columna      |   count |   mean |   mediana |   moda |    std |    min |     max |
|:-------------|--------:|-------:|----------:|-------:|-------:|-------:|--------:|
| edad         |    6500 |  36.31 |     36    |  18    |  11.36 |  18    |   79    |
| venta_total  |    6500 | 206.24 |    137.35 |  98    | 215.55 |   9    | 3169    |
| n_compras    |    6500 |   5.09 |      4    |   2    |   3.96 |   1    |   25    |
| monto_compra |    6500 |  39.79 |     35.76 |  37.15 |  19.52 |   7.24 |  199.35 |
| tiempo_seg   |    6500 | 767.38 |    768    | 852    | 181.75 | 180    | 1443    |

## 8. Analisis de outliers

Se aplico el criterio del rango intercuartilico (valores fuera de
[Q1 - 1.5*IQR, Q3 + 1.5*IQR]):

| columna      |     q1 |     q3 |   limite_inferior |   limite_superior |   outliers |   porcentaje |
|:-------------|-------:|-------:|------------------:|------------------:|-----------:|-------------:|
| edad         |  28    |  44    |              4    |             68    |         27 |         0.42 |
| venta_total  |  69.1  | 266.6  |           -227.15 |            562.85 |        418 |         6.43 |
| n_compras    |   2    |   7    |             -5.5  |             14.5  |        216 |         3.32 |
| monto_compra |  26.22 |  48.56 |             -7.28 |             82.06 |        229 |         3.52 |
| tiempo_seg   | 645    | 886    |            283.5  |           1247.5  |         50 |         0.77 |

**Decision: los outliers se conservan.** El criterio del IQR marca como atipicos
los valores altos de `venta_total` (hasta Q3,169), pero se trata de clientes con
alto volumen de compra, no de errores de captura: son internamente consistentes
(edad valida, fecha valida, metodo de pago valido) y representan justamente al
segmento de mayor valor comercial. Eliminarlos sesgaria a la baja el analisis de
ventas y borraria a los clientes mas rentables, que son los de mayor interes
para las recomendaciones de negocio del informe.

## 9. Distribucion de las variables categoricas

| variable       |   codigo | etiqueta           |   registros |   porcentaje |
|:---------------|---------:|:-------------------|------------:|-------------:|
| genero         |        0 | Masculino          |        3372 |        51.88 |
| genero         |        1 | Femenino           |        3128 |        48.12 |
| metodo_pago_id |        0 | Efectivo           |        1207 |        18.57 |
| metodo_pago_id |        1 | Tarjeta de Credito |        3827 |        58.88 |
| metodo_pago_id |        2 | Tarjeta de Debito  |        1466 |        22.55 |
| navegador_id   |        0 | Tienda Fisica      |        3523 |        54.2  |
| navegador_id   |        1 | Navegador 1        |        1273 |        19.58 |
| navegador_id   |        2 | Navegador 2        |         847 |        13.03 |
| navegador_id   |        3 | Navegador 3        |         660 |        10.15 |
| navegador_id   |        4 | Navegador 4        |         197 |         3.03 |
| boletin        |        0 | No                 |        3579 |        55.06 |
| boletin        |        1 | Si                 |        2921 |        44.94 |
| vale           |        0 | No                 |        5246 |        80.71 |
| vale           |        1 | Si                 |        1254 |        19.29 |

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
representa el **54.2%**
de los registros, pese a que el enunciado describe el archivo como ventas
online. Se conserva tal cual y se debe considerar al comparar tienda fisica
contra navegadores web en el analisis de canales.

---

## Resumen del proceso

| Paso | Accion | Resultado |
|---|---|---|
| 1 | Extraccion del CSV con separador y fecha explicitos | 6,500 filas leidas |
| 2 | Verificacion de valores faltantes | 0 nulos |
| 3 | Verificacion de duplicados | 0 duplicados |
| 4 | Validacion de dominios categoricos | Todos los codigos validos |
| 5 | Validacion de rangos | Sin valores imposibles |
| 6 | Tipificacion de columnas | 12 columnas tipificadas |
| 7 | Analisis de outliers | Reportados y conservados |
| 8 | Exportacion | `data/processed/ventas_limpias.csv` |

**Registros de salida: 6,500** (no se elimino ningun registro).

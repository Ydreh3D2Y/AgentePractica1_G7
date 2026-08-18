# Practica 1 - Sistemas Organizacionales y Gerenciales 2

Analisis de ventas online 2021 con base de datos relacional en la nube y agente
conversacional de IA.

## Estructura del proyecto

```
.
├── data/
│   ├── raw/Venta_online_c.csv          # dataset original (no se modifica)
│   └── processed/ventas_limpias.csv    # salida de la limpieza
├── src/
│   ├── config.py                       # rutas, catalogos y conexion
│   ├── limpieza.py                     # Fase 1: preparacion de datos
│   ├── probar_conexion.py              # Fase 3: diagnostico de conexion
│   ├── db.py                           # Fase 4: capa de acceso a los datos
│   └── visualizaciones.py              # Puntos 2c y 6: genera ocho graficas
├── scripts/
│   ├── modelo.sql                      # Fase 2: DDL de la base de datos
│   ├── carga_1_crear_staging.sql       # Fase 3: carga manual, paso 1 de 3
│   └── carga_2_traspaso.sql            # Fase 3: carga manual, paso 3 de 3
├── docs/
│   └── perfilado.md                    # evidencia del proceso de limpieza
├── requirements.txt
└── .env.example
```

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # y rellenar con las credenciales de Supabase
```

> El archivo `.env` contiene la contrasena de la base de datos y esta en
> `.gitignore`. **Nunca debe subirse a GitHub.**

## Ejecucion

```bash
python src/limpieza.py           # genera ventas_limpias.csv y docs/perfilado.md
python src/probar_conexion.py    # verifica que la conexion a Supabase funcione
python src/visualizaciones.py    # genera las ocho graficas desde Supabase
```

Luego, en el SQL Editor de Supabase (o DataGrip), ejecutar `scripts/modelo.sql`
para crear las tablas.

### Carga de datos (manual, en 3 pasos)

La carga se hace en tres archivos **separados a proposito**, para que no se
puedan correr de una sola vez. El paso 2 es una accion de mouse (importar un
CSV) y no una sentencia SQL, asi que si los tres pasos estuvieran en un solo
archivo, "ejecutar todo el script" saltaria la importacion en silencio y las
tablas finales quedarian vacias.

1. **`scripts/carga_1_crear_staging.sql`** — crea una tabla puente
   (`staging_ventas`) con las mismas 12 columnas del CSV limpio, en el mismo
   orden.
2. **Importar el CSV manualmente en DataGrip:** click derecho sobre
   `staging_ventas` → *Import Data from File...* → seleccionar
   `data/processed/ventas_limpias.csv` → confirmar `Format = CSV`, header
   activado, delimitador coma → Import.
   Verificar antes de seguir: `SELECT count(*) FROM staging_ventas;` debe
   devolver **6500**. Si devuelve 0, este paso no se hizo.
3. **`scripts/carga_2_traspaso.sql`** — reparte los datos de `staging_ventas`
   hacia `cliente` y `compra`, verifica conteos y sumas de control, y al
   final elimina `staging_ventas`.

Sumas de control esperadas tras la carga (validadas contra estos mismos datos
en un Postgres real durante la Fase 2): `suma venta_total = 1340575.80`,
`suma monto_compra = 258615.861`.


## Capa de acceso a datos

El modulo `src/db.py` expone las funciones de consulta a la base de datos.
**Es el punto unico de acceso a los datos**, en lugar de leer el CSV
directamente: el analisis y las graficas se construyen sobre estas funciones,
y el agente de IA las expone como herramientas del MCP Server sin
reimplementar la logica. Asi el informe y el agente reportan los mismos
numeros.

### Uso

```python
import db

df = db.ventas_por_mes()        # devuelve un pandas.DataFrame
print(df)

resultado = db.correlacion_venta_edad()   # devuelve un dict (Pearson r, p-valor)
print(resultado)
```

Para exponer cualquier funcion como herramienta MCP, conviertan el DataFrame a
JSON con `df.to_dict(orient="records")`; los resultados de correlacion ya son
un `dict` y se serializan directo.

### Mapeo de funciones al enunciado (seccion 3.2)

| Punto | Funcion | Devuelve |
|---|---|---|
| 2a | `cargar_ventas()` | dataset completo (1 fila por compra) |
| 2b | `estadisticas_basicas()` | media, mediana, moda de las variables numericas |
| 2c | `distribucion_mes()`, `distribucion_metodo_pago()`, `distribucion_navegador()`, `distribucion_boletin()`, `distribucion_vale()` | distribucion por cada variable pedida |
| 3a | `ventas_por_mes()`, `meses_extremos()` | ventas por mes; mes de mayor/menor venta |
| 3b | `popularidad_navegador()`, `navegadores_extremos()` | navegador mas y menos usado |
| 3c | `ventas_por_metodo_pago()`, `total_efectivo_vs_otros()` | total pagado en efectivo vs. tarjeta |
| 3d | `boletin_vale_por_mes()`, `meses_maximos_boletin_vale()` | compras mensuales y meses con mayor uso de boletin/vale |
| 4a | `segmentacion_edad()` | patrones de compra por rango de edad |
| 4b | `comparacion_genero()` | patrones de compra por genero |
| 4c | `segmentacion_boletin_vale()` | patrones de compra por boletin y vale |
| 5a | `correlacion_venta_edad()` | Pearson r entre venta_total y edad |
| 5b | `correlacion_genero_metodo_pago()` | chi-cuadrado y V de Cramer, genero x metodo de pago |
| 5c | `correlacion_boletin_vale()` | chi-cuadrado y V de Cramer, boletin x vale |

Prueba de humo contra la base de datos real (ejecuta las 21 funciones y
reporta si alguna falla):

```bash
python src/db.py
```

## Visualizaciones

El modulo `src/visualizaciones.py` reutiliza exclusivamente las funciones de
`src/db.py`. No lee el CSV ni contiene consultas SQL nuevas. Al ejecutarlo crea
automaticamente `output/graficos/` y guarda ocho archivos PNG listos para
incorporarlos al informe.

No requiere cambios adicionales en Supabase. Antes de ejecutarlo deben estar
activos el entorno virtual y las variables de conexion del archivo `.env`.

### Generacion

Desde la raiz del proyecto:

```bash
python src/visualizaciones.py
```

Una ejecucion correcta muestra ocho rutas que comienzan con `OK` y termina con:

```text
OK - visualizaciones generadas correctamente
```

Si las imagenes ya existen, se vuelven a generar con los mismos nombres. No es
necesario ejecutar otra vez `modelo.sql`, los scripts de carga ni instrucciones
adicionales en Supabase.

### Archivos generados

| Archivo | Contenido | Seccion del informe |
|---|---|---|
| `01_ventas_por_mes.png` | Monto total de compra por mes y meses extremos | 6.1 |
| `02_metodos_pago.png` | Distribucion de compras por metodo de pago | 6.2 |
| `03_navegadores.png` | Popularidad de navegadores y tienda fisica | 6.3 |
| `04_distribucion_boletin_vale.png` | Distribucion general de boletin y vale | 6.4 |
| `05_boletin_vale_por_mes.png` | Compras con boletin y vale por mes | 6.5 |
| `06_segmentacion_edad.png` | Venta promedio por rango de edad | 6.6 |
| `07_comparacion_genero.png` | Venta y compras promedio por genero | 6.7 |
| `08_correlacion_edad_venta.png` | Relacion entre edad y venta total | 6.8 |

La seccion 6.12 del informe solo documenta la correspondencia entre las figuras
y los requisitos del enunciado. Las imagenes no deben insertarse nuevamente en
esa seccion.

### Comprobacion

Primero se pueden validar las consultas con:

```bash
python src/db.py
```

La prueba debe finalizar con `OK - todas las funciones respondieron
correctamente`. Despues de generar las graficas, en PowerShell se puede comprobar
la cantidad de archivos con:

```powershell
(Get-ChildItem output/graficos -Filter *.png).Count
```

El resultado esperado es `8`. Tambien se deben abrir las imagenes y comprobar
que no existan etiquetas recortadas, leyendas superpuestas ni texto ilegible.

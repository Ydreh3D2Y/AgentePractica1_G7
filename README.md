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
│   ├── visualizaciones.py              # Puntos 2c y 6: genera ocho graficas
│   └── mcp_server.py                    # MCP Server: publica los puntos 2 a 6
├── tests/
│   └── probar_mcp.py                    # prueba de integracion del MCP
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
python tests/probar_mcp.py       # comprueba el servidor y sus herramientas
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

## MCP Server

El archivo `src/mcp_server.py` publica mediante Model Context Protocol los
resultados de los puntos 2 a 6. Es una capa de solo lectura: reutiliza las
funciones de `src/db.py`, no contiene nuevas consultas SQL y no modifica datos.

Se usa el transporte `stdio`. El cliente, posteriormente Google ADK, inicia el
servidor como un subproceso y se comunica por la entrada y salida estandar. Por
eso no se configura un puerto, una URL de servidor MCP ni autenticacion MCP para
la ejecucion local.

### Requisitos
Python 3.10 o posterior.

### Herramientas publicadas

| Punto | Herramienta MCP | Contenido |
|---|---|---|
| 2a | `obtener_datos_ventas` | Dataset paginado, con un maximo de 200 filas por llamada |
| 2b | `obtener_estadisticas_basicas` | Media, mediana, moda, desviacion y rango |
| 2c | `obtener_distribuciones_ventas` | Distribuciones por mes, pago, navegador, boletin y vale |
| 3a | `analizar_ventas_mensuales` | Ventas mensuales y meses extremos |
| 3b | `analizar_popularidad_navegadores` | Uso por canal y navegadores extremos |
| 3c | `analizar_metodos_pago` | Desglose de pagos y efectivo contra tarjetas |
| 3d | `analizar_boletin_vale_por_mes` | Comportamiento mensual y meses maximos |
| 4a | `segmentar_clientes_por_edad` | Patrones por rango de edad |
| 4b | `comparar_comportamiento_por_genero` | Patrones por genero |
| 4c | `segmentar_clientes_por_boletin_vale` | Patrones por boletin y vale |
| 5a | `analizar_correlacion_edad_venta` | Pearson entre edad y venta total |
| 5b | `analizar_asociacion_genero_metodo_pago` | Chi-cuadrado y V de Cramer |
| 5c | `analizar_asociacion_boletin_vale` | Chi-cuadrado y V de Cramer |
| 6 | `listar_visualizaciones` | Catalogo y disponibilidad de las ocho graficas |
| 6 | `obtener_visualizacion` | Una grafica PNG como contenido de imagen MCP |

### Comprobacion automatica

La siguiente prueba usa un cliente MCP en memoria. Descubre las herramientas a
traves del protocolo y llama a las quince, incluida una visualizacion:

```bash
python tests/probar_mcp.py
```

Debe terminar con:

```text
OK - todas las herramientas MCP respondieron correctamente
```

Esta prueba si consulta Supabase. No inicia puertos ni utiliza un modelo de IA.

### Ejecucion directa

```bash
python src/mcp_server.py
```

Al ejecutarlo directamente la terminal queda esperando sin mostrar un menu. Es
el comportamiento normal de un servidor `stdio`, espera que un cliente MCP le
envie mensajes. Se detiene con `Ctrl+C`.

Para inspeccion interactiva se puede usar de manera opcional el Inspector del
SDK:

```bash
mcp dev src/mcp_server.py
```

El Inspector puede requerir Node.js y `npx`. No es necesario para la prueba
automatizada ni para la integracion con Google ADK.

### Contrato para la integracion con Google ADK

El agente debe iniciar el servidor con el Python del mismo entorno virtual y
la ruta absoluta de `src/mcp_server.py`. En Windows, los parametros equivalen a:

```python
StdioServerParameters(
    command=r"C:\ruta\al\proyecto\.venv\Scripts\python.exe",
    args=[r"C:\ruta\al\proyecto\src\mcp_server.py"],
)
```

No es necesario pasar `DATABASE_URL` en esos parametros porque `src/config.py`
carga el `.env` utilizando una ruta absoluta basada en la raiz del proyecto.
El servidor no debe imprimir mensajes propios en la salida estandar, pues ese
canal esta reservado para el protocolo MCP.

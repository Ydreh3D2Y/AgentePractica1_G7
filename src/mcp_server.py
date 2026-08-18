"""Servidor MCP de consulta para el analisis de ventas

El servidor reutiliza la capa de acceso de ``db.py`` y no ejecuta escrituras
en Supabase
El transporte predeterminado es stdio, pensado para que Google ADK inicie este archivo 
como un subproceso local

Inicio manual opcional, solo para diagnostico desde la raiz del proyecto:
    python src/mcp_server.py

En el uso normal no se inicia manualmente. El cliente MCP, por ejemplo Google
ADK, ejecuta este archivo como subproceso y se comunica mediante stdio.
"""

from __future__ import annotations

import base64
import json
from decimal import Decimal
from pathlib import Path
from typing import Any

import pandas as pd
from mcp.server.mcpserver import MCPServer
from mcp.types import CallToolResult, ImageContent, TextContent

import config
import db


mcp = MCPServer(
    "analisis-ventas-practica1",
    instructions=(
        "Herramientas de solo lectura para consultar el analisis de ventas de "
        "2021. Usa los resultados entregados por las herramientas y no inventes "
        "cifras. Una asociacion estadistica no demuestra causalidad."
    ),
)


VISUALIZACIONES = {
    "ventas_por_mes": {
        "archivo": "01_ventas_por_mes.png",
        "descripcion": "Monto total de compra por mes y meses extremos.",
        "punto": "3a y 6",
    },
    "metodos_pago": {
        "archivo": "02_metodos_pago.png",
        "descripcion": "Distribucion de compras por metodo de pago.",
        "punto": "2c, 3c y 6",
    },
    "navegadores": {
        "archivo": "03_navegadores.png",
        "descripcion": "Popularidad de navegadores y tienda fisica.",
        "punto": "2c, 3b y 6",
    },
    "distribucion_boletin_vale": {
        "archivo": "04_distribucion_boletin_vale.png",
        "descripcion": "Distribucion general de clientes por boletin y vale.",
        "punto": "2c y 6",
    },
    "boletin_vale_por_mes": {
        "archivo": "05_boletin_vale_por_mes.png",
        "descripcion": "Compras asociadas a boletin y vale por mes.",
        "punto": "3d y 6",
    },
    "segmentacion_edad": {
        "archivo": "06_segmentacion_edad.png",
        "descripcion": "Venta promedio por rango de edad.",
        "punto": "4a y 6",
    },
    "comparacion_genero": {
        "archivo": "07_comparacion_genero.png",
        "descripcion": "Venta y compras promedio por genero.",
        "punto": "4b y 6",
    },
    "correlacion_edad_venta": {
        "archivo": "08_correlacion_edad_venta.png",
        "descripcion": "Relacion entre edad y venta total.",
        "punto": "5a y 6",
    },
}


def _registros(datos: pd.DataFrame) -> list[dict[str, Any]]:
    """Convierte un DataFrame a valores JSON validos, incluidos fechas y nulos"""
    return json.loads(datos.to_json(orient="records", date_format="iso"))


def _objeto_json(valor: Any) -> Any:
    """Normaliza diccionarios con escalares de pandas, numpy o Decimal."""
    def convertir(objeto: Any) -> Any:
        if isinstance(objeto, (pd.Timestamp, Path)):
            return str(objeto)
        if isinstance(objeto, Decimal):
            return float(objeto)
        if hasattr(objeto, "item"):
            return objeto.item()
        raise TypeError(f"Tipo no serializable: {type(objeto).__name__}")

    return json.loads(json.dumps(valor, default=convertir, allow_nan=False))


def _respuesta_tabla(punto: str, datos: pd.DataFrame) -> dict[str, Any]:
    return {
        "punto_enunciado": punto,
        "cantidad_filas": len(datos),
        "columnas": list(datos.columns),
        "datos": _registros(datos),
    }


@mcp.tool()
def obtener_datos_ventas(limite: int = 50, desplazamiento: int = 0) -> dict[str, Any]:
    """Obtiene una pagina del dataset de ventas del punto 2a
    Usar limite entre 1 y 200 y desplazamiento desde 0 para explorar los datos
    ! mejor solicitar páginas pequeñas no las 6500 filas de una vez
    """
    if not 1 <= limite <= 200:
        raise ValueError("limite debe estar entre 1 y 200")
    if desplazamiento < 0:
        raise ValueError("desplazamiento no puede ser negativo")

    ventas = db.cargar_ventas()
    pagina = ventas.iloc[desplazamiento : desplazamiento + limite]
    respuesta = _respuesta_tabla("2a", pagina)
    respuesta.update(
        {
            "total_filas": len(ventas),
            "limite": limite,
            "desplazamiento": desplazamiento,
            "hay_mas": desplazamiento + len(pagina) < len(ventas),
        }
    )
    return respuesta


@mcp.tool()
def obtener_estadisticas_basicas() -> dict[str, Any]:
    """Calcula media, mediana, moda, desviacion y rango del punto 2b"""
    return _respuesta_tabla("2b", db.estadisticas_basicas())


@mcp.tool()
def obtener_distribuciones_ventas() -> dict[str, Any]:
    """Obtiene las distribuciones del punto 2c por mes, pago, canal, boletin y vale"""
    return {
        "punto_enunciado": "2c",
        "por_mes": _registros(db.distribucion_mes()),
        "por_metodo_pago": _registros(db.distribucion_metodo_pago()),
        "por_navegador": _registros(db.distribucion_navegador()),
        "por_boletin": _registros(db.distribucion_boletin()),
        "por_vale": _registros(db.distribucion_vale()),
    }


@mcp.tool()
def analizar_ventas_mensuales() -> dict[str, Any]:
    """Analiza ventas por mes e identifica los meses mayor y menor del punto 3a"""
    return {
        "punto_enunciado": "3a",
        "ventas_por_mes": _registros(db.ventas_por_mes()),
        "meses_extremos": _objeto_json(db.meses_extremos()),
    }


@mcp.tool()
def analizar_popularidad_navegadores() -> dict[str, Any]:
    """Compara canales e identifica el mas y el menos usado del punto 3b"""
    return {
        "punto_enunciado": "3b",
        "popularidad": _registros(db.popularidad_navegador()),
        "extremos": _objeto_json(db.navegadores_extremos()),
    }


@mcp.tool()
def analizar_metodos_pago() -> dict[str, Any]:
    """Compara efectivo contra tarjetas y detalla cada metodo para el punto 3c"""
    return {
        "punto_enunciado": "3c",
        "por_metodo": _registros(db.ventas_por_metodo_pago()),
        "efectivo_vs_otros": _registros(db.total_efectivo_vs_otros()),
    }


@mcp.tool()
def analizar_boletin_vale_por_mes() -> dict[str, Any]:
    """Muestra boletin y vale por mes e identifica sus maximos para el punto 3d"""
    return {
        "punto_enunciado": "3d",
        "por_mes": _registros(db.boletin_vale_por_mes()),
        "meses_maximos": _objeto_json(db.meses_maximos_boletin_vale()),
    }


@mcp.tool()
def segmentar_clientes_por_edad() -> dict[str, Any]:
    """Compara patrones de compra por rangos de edad para el punto 4a"""
    return _respuesta_tabla("4a", db.segmentacion_edad())


@mcp.tool()
def comparar_comportamiento_por_genero() -> dict[str, Any]:
    """Compara patrones de compra entre generos para el punto 4b"""
    return _respuesta_tabla("4b", db.comparacion_genero())


@mcp.tool()
def segmentar_clientes_por_boletin_vale() -> dict[str, Any]:
    """Compara patrones por combinacion de boletin y vale para el punto 4c"""
    return _respuesta_tabla("4c", db.segmentacion_boletin_vale())


@mcp.tool()
def analizar_correlacion_edad_venta() -> dict[str, Any]:
    """Calcula Pearson entre edad y venta total para el punto 5a"""
    return {
        "punto_enunciado": "5a",
        "resultado": _objeto_json(db.correlacion_venta_edad()),
        "advertencia": "La significancia estadistica no implica una relacion de magnitud importante.",
    }


@mcp.tool()
def analizar_asociacion_genero_metodo_pago() -> dict[str, Any]:
    """Calcula chi-cuadrado y V de Cramer entre genero y pago para el punto 5b"""
    return {
        "punto_enunciado": "5b",
        "resultado": _objeto_json(db.correlacion_genero_metodo_pago()),
        "advertencia": "Una asociacion estadistica no demuestra causalidad.",
    }


@mcp.tool()
def analizar_asociacion_boletin_vale() -> dict[str, Any]:
    """Calcula chi-cuadrado y V de Cramer entre boletin y vale para el punto 5c"""
    return {
        "punto_enunciado": "5c",
        "resultado": _objeto_json(db.correlacion_boletin_vale()),
        "advertencia": "Una asociacion estadistica no demuestra causalidad.",
    }


@mcp.tool()
def listar_visualizaciones() -> dict[str, Any]:
    """Lista las ocho graficas del punto 6, su proposito y disponibilidad local"""
    carpeta = config.RAIZ / "output" / "graficos"
    graficas = []
    for nombre, metadata in VISUALIZACIONES.items():
        ruta = carpeta / metadata["archivo"]
        graficas.append(
            {
                "nombre": nombre,
                **metadata,
                "disponible": ruta.is_file(),
                "ruta_relativa": f"output/graficos/{metadata['archivo']}",
            }
        )
    return {"punto_enunciado": "6", "cantidad": len(graficas), "graficas": graficas}


@mcp.tool()
def obtener_visualizacion(nombre: str) -> CallToolResult:
    """Devuelve como imagen una grafica del punto 6
    Primero usa listar_visualizaciones para conocer los nombres permitidos
    """
    if nombre not in VISUALIZACIONES:
        permitidos = ", ".join(VISUALIZACIONES)
        raise ValueError(f"Visualizacion desconocida. Nombres permitidos: {permitidos}")

    metadata = VISUALIZACIONES[nombre]
    ruta = config.RAIZ / "output" / "graficos" / metadata["archivo"]
    if not ruta.is_file():
        raise FileNotFoundError(
            "La grafica no existe. Ejecuta primero: python src/visualizaciones.py"
        )

    datos_base64 = base64.b64encode(ruta.read_bytes()).decode("ascii")
    return CallToolResult(
        content=[
            TextContent(type="text", text=metadata["descripcion"]),
            ImageContent(type="image", data=datos_base64, mime_type="image/png"),
        ],
        structured_content={
            "punto_enunciado": "6",
            "nombre": nombre,
            "archivo": metadata["archivo"],
            "descripcion": metadata["descripcion"],
        },
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")

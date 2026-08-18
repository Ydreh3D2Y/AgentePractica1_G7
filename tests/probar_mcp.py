"""Prueba de humo del servidor MCP sin iniciar un puerto ni Google ADK"""

import asyncio
import sys
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent
SRC = RAIZ / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from mcp import Client  # noqa: E402

from mcp_server import mcp  # noqa: E402


PRUEBAS = [
    ("obtener_datos_ventas", {"limite": 3, "desplazamiento": 0}),
    ("obtener_estadisticas_basicas", {}),
    ("obtener_distribuciones_ventas", {}),
    ("analizar_ventas_mensuales", {}),
    ("analizar_popularidad_navegadores", {}),
    ("analizar_metodos_pago", {}),
    ("analizar_boletin_vale_por_mes", {}),
    ("segmentar_clientes_por_edad", {}),
    ("comparar_comportamiento_por_genero", {}),
    ("segmentar_clientes_por_boletin_vale", {}),
    ("analizar_correlacion_edad_venta", {}),
    ("analizar_asociacion_genero_metodo_pago", {}),
    ("analizar_asociacion_boletin_vale", {}),
    ("listar_visualizaciones", {}),
    ("obtener_visualizacion", {"nombre": "ventas_por_mes"}),
]


async def probar() -> None:
    """Descubre e invoca todas las herramientas mediante el protocolo MCP"""
    async with Client(mcp, raise_exceptions=True) as cliente:
        resultado_lista = await cliente.list_tools()
        disponibles = {herramienta.name for herramienta in resultado_lista.tools}

        print("Prueba del servidor MCP")
        print("=" * 60)
        print(f"Herramientas descubiertas: {len(disponibles)}")

        for nombre, argumentos in PRUEBAS:
            if nombre not in disponibles:
                raise RuntimeError(f"La herramienta {nombre} no fue publicada")
            resultado = await cliente.call_tool(nombre, argumentos)
            if resultado.is_error:
                raise RuntimeError(f"Fallo {nombre}: {resultado.content}")
            print(f"OK  {nombre}")

        print("=" * 60)
        print("OK - todas las herramientas MCP respondieron correctamente")


if __name__ == "__main__":
    asyncio.run(probar())

"""Visualizaciones de los puntos 2c y 6 del enunciado
Todas las fuentes de datos provienen de db.py para mantener una unica logica de acceso a Supabase

generación de graficas con:
    python src/visualizaciones.py

Salida:
    output/graficos/*.png
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

import db


RAIZ = Path(__file__).resolve().parent.parent
DIRECTORIO_GRAFICOS = RAIZ / "output" / "graficos"

COLOR_PRINCIPAL = "#315A7D"
COLOR_SECUNDARIO = "#C58A2A"
COLOR_TERCIARIO = "#7A8793"


def _configurar_estilo() -> None:
    """Aplica una presentacion consistente y legible para todo el informe."""
    plt.rcParams.update(
        {
            "figure.figsize": (10, 6),
            "figure.dpi": 120,
            "savefig.dpi": 180,
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "DejaVu Sans"],
            "font.size": 10,
            "axes.titlesize": 14,
            "axes.labelsize": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "legend.frameon": False,
        }
    )


def _guardar(figura: Figure, nombre: str) -> Path:
    """Guarda una figura sin recortes y libera sus recursos."""
    DIRECTORIO_GRAFICOS.mkdir(parents=True, exist_ok=True)
    ruta = DIRECTORIO_GRAFICOS / nombre
    figura.tight_layout()
    figura.savefig(ruta, bbox_inches="tight", facecolor="white")
    plt.close(figura)
    return ruta


def grafico_ventas_por_mes() -> Path:
    """Figura 2. Evolucion mensual del monto de compra."""
    datos = db.ventas_por_mes().copy()
    datos = datos.sort_values("mes")

    figura, eje = plt.subplots()
    eje.plot(
        datos["mes_nombre"],
        datos["monto_total"],
        color=COLOR_PRINCIPAL,
        marker="o",
        linewidth=2.2,
    )

    mayor = datos.loc[datos["monto_total"].idxmax()]
    menor = datos.loc[datos["monto_total"].idxmin()]
    eje.scatter(
        [mayor["mes_nombre"], menor["mes_nombre"]],
        [mayor["monto_total"], menor["monto_total"]],
        color=[COLOR_SECUNDARIO, COLOR_TERCIARIO],
        s=80,
        zorder=3,
    )
    eje.annotate(
        f"Mayor: Q{mayor['monto_total']:,.2f}",
        (mayor["mes_nombre"], mayor["monto_total"]),
        xytext=(8, 10),
        textcoords="offset points",
    )
    eje.annotate(
        f"Menor: Q{menor['monto_total']:,.2f}",
        (menor["mes_nombre"], menor["monto_total"]),
        xytext=(-10, 15),
        textcoords="offset points",
        horizontalalignment="right",
    )
    eje.set_title("Monto de compra por mes")
    eje.set_xlabel("Mes")
    eje.set_ylabel("Monto total en quetzales")
    eje.tick_params(axis="x", rotation=45)
    eje.yaxis.set_major_formatter(lambda valor, _: f"Q{valor:,.0f}")
    return _guardar(figura, "01_ventas_por_mes.png")


def grafico_metodos_pago() -> Path:
    """Figura 3. Cantidad de compras por metodo de pago."""
    datos = db.distribucion_metodo_pago().copy()
    datos = datos.sort_values("compras", ascending=False)

    figura, eje = plt.subplots()
    barras = eje.bar(
        datos["metodo_pago"],
        datos["compras"],
        color=[COLOR_PRINCIPAL, COLOR_SECUNDARIO, COLOR_TERCIARIO],
    )
    etiquetas = [
        f"{int(compras):,}\n{porcentaje:.2f}%"
        for compras, porcentaje in zip(datos["compras"], datos["porcentaje"])
    ]
    eje.bar_label(barras, labels=etiquetas, padding=4)
    eje.set_title("Distribucion de compras por metodo de pago")
    eje.set_xlabel("Metodo de pago")
    eje.set_ylabel("Cantidad de compras")
    eje.set_ylim(0, datos["compras"].max() * 1.18)
    return _guardar(figura, "02_metodos_pago.png")


def grafico_navegadores() -> Path:
    """Figura 4. Popularidad de los canales de compra."""
    datos = db.distribucion_navegador().copy()
    datos = datos.sort_values("compras", ascending=True)

    figura, eje = plt.subplots()
    colores = [
        COLOR_SECUNDARIO if nombre == "Tienda Fisica" else COLOR_PRINCIPAL
        for nombre in datos["navegador"]
    ]
    barras = eje.barh(datos["navegador"], datos["compras"], color=colores)
    etiquetas = [
        f"{int(compras):,} ({porcentaje:.2f}%)"
        for compras, porcentaje in zip(datos["compras"], datos["porcentaje"])
    ]
    eje.bar_label(barras, labels=etiquetas, padding=4)
    eje.set_title("Popularidad de navegadores y tienda fisica")
    eje.set_xlabel("Cantidad de compras")
    eje.set_ylabel("Canal")
    eje.set_xlim(0, datos["compras"].max() * 1.22)
    return _guardar(figura, "03_navegadores.png")


def grafico_distribucion_boletin_vale() -> Path:
    """Figura 5. Distribucion general de clientes por boletin y vale."""
    conteos_boletin = db.distribucion_boletin().set_index("boletin")["clientes"]
    conteos_vale = db.distribucion_vale().set_index("vale")["clientes"]
    resumen = pd.DataFrame({"Estado": ["No", "Si"]})
    resumen["Boletin"] = resumen["Estado"].map(conteos_boletin).astype(int)
    resumen["Vale"] = resumen["Estado"].map(conteos_vale).astype(int)

    figura, eje = plt.subplots()
    posiciones = range(len(resumen))
    ancho = 0.36
    barras_boletin = eje.bar(
        [posicion - ancho / 2 for posicion in posiciones],
        resumen["Boletin"],
        width=ancho,
        label="Boletin",
        color=COLOR_PRINCIPAL,
    )
    barras_vale = eje.bar(
        [posicion + ancho / 2 for posicion in posiciones],
        resumen["Vale"],
        width=ancho,
        label="Vale",
        color=COLOR_SECUNDARIO,
    )
    eje.bar_label(barras_boletin, fmt="{:,.0f}", padding=3)
    eje.bar_label(barras_vale, fmt="{:,.0f}", padding=3)
    eje.set_xticks(list(posiciones), resumen["Estado"])
    eje.set_title("Distribucion de clientes por boletin y vale")
    eje.set_xlabel("Estado")
    eje.set_ylabel("Cantidad de clientes")
    eje.legend()
    eje.set_ylim(0, resumen[["Boletin", "Vale"]].to_numpy().max() * 1.14)
    return _guardar(figura, "04_distribucion_boletin_vale.png")


def grafico_boletin_vale_por_mes() -> Path:
    """Figura 6. Uso mensual de boletines y vales."""
    datos = db.boletin_vale_por_mes().copy()
    datos = datos.sort_values("mes")

    figura, eje = plt.subplots()
    eje.plot(
        datos["mes_nombre"],
        datos["compras_con_boletin"],
        marker="o",
        linewidth=2,
        color=COLOR_PRINCIPAL,
        label="Compras con boletin",
    )
    eje.plot(
        datos["mes_nombre"],
        datos["compras_con_vale"],
        marker="s",
        linewidth=2,
        color=COLOR_SECUNDARIO,
        label="Compras con vale",
    )
    eje.set_title("Compras con boletin y vale por mes")
    eje.set_xlabel("Mes")
    eje.set_ylabel("Cantidad de compras")
    eje.tick_params(axis="x", rotation=45)
    eje.legend()
    return _guardar(figura, "05_boletin_vale_por_mes.png")


def grafico_segmentacion_edad() -> Path:
    """Figura 7. Venta promedio por rango de edad."""
    datos = db.segmentacion_edad().copy()

    figura, eje = plt.subplots()
    barras = eje.bar(
        datos["rango_edad"],
        datos["venta_promedio"],
        color=COLOR_PRINCIPAL,
    )
    eje.bar_label(barras, labels=[f"Q{valor:,.2f}" for valor in datos["venta_promedio"]], padding=3)
    eje.set_title("Venta promedio por rango de edad")
    eje.set_xlabel("Rango de edad")
    eje.set_ylabel("Venta promedio en quetzales")
    eje.yaxis.set_major_formatter(lambda valor, _: f"Q{valor:,.0f}")
    eje.set_ylim(0, datos["venta_promedio"].max() * 1.15)
    return _guardar(figura, "06_segmentacion_edad.png")


def grafico_comparacion_genero() -> Path:
    """Figura 8. Venta y compras promedio por genero."""
    datos = db.comparacion_genero().copy()

    figura, eje_venta = plt.subplots()
    posiciones = list(range(len(datos)))
    barras = eje_venta.bar(
        posiciones,
        datos["venta_promedio"],
        width=0.55,
        color=[COLOR_PRINCIPAL, COLOR_SECUNDARIO],
    )
    eje_venta.bar_label(
        barras,
        labels=[f"Q{valor:,.2f}" for valor in datos["venta_promedio"]],
        padding=3,
    )
    eje_venta.set_xticks(posiciones, datos["genero"])
    eje_venta.set_title("Comportamiento de compra por genero")
    eje_venta.set_xlabel("Genero")
    eje_venta.set_ylabel("Venta promedio en quetzales")
    eje_venta.yaxis.set_major_formatter(lambda valor, _: f"Q{valor:,.0f}")

    eje_compras = eje_venta.twinx()
    eje_compras.plot(
        posiciones,
        datos["compras_promedio"],
        color=COLOR_TERCIARIO,
        marker="o",
        linewidth=2,
        label="Compras promedio",
    )
    eje_compras.set_ylabel("Compras promedio")
    eje_compras.spines["right"].set_visible(True)
    eje_compras.legend(loc="upper center", bbox_to_anchor=(0.5, -0.12))
    return _guardar(figura, "07_comparacion_genero.png")


def grafico_correlacion_edad_venta() -> Path:
    """Figura 9. Dispersion entre edad y venta total."""
    datos = db.cargar_ventas()[["id_cliente", "edad", "venta_total"]].copy()
    datos = datos.drop_duplicates(subset=["id_cliente"])

    figura, eje = plt.subplots()
    eje.scatter(
        datos["edad"],
        datos["venta_total"],
        s=16,
        alpha=0.28,
        color=COLOR_PRINCIPAL,
        edgecolors="none",
    )

    coeficientes = pd.Series(datos["venta_total"]).corr(pd.Series(datos["edad"]))
    pendiente = datos[["edad", "venta_total"]].cov().iloc[0, 1] / datos["edad"].var()
    intercepto = datos["venta_total"].mean() - pendiente * datos["edad"].mean()
    edades = pd.Series([datos["edad"].min(), datos["edad"].max()])
    eje.plot(
        edades,
        intercepto + pendiente * edades,
        color=COLOR_SECUNDARIO,
        linewidth=2,
        label=f"Tendencia, r = {coeficientes:.4f}",
    )
    eje.set_title("Relacion entre edad y venta total")
    eje.set_xlabel("Edad")
    eje.set_ylabel("Venta total en quetzales")
    eje.yaxis.set_major_formatter(lambda valor, _: f"Q{valor:,.0f}")
    eje.legend()
    return _guardar(figura, "08_correlacion_edad_venta.png")


def generar_todas() -> list[Path]:
    """Genera las ocho figuras del aporte de visualizacion."""
    _configurar_estilo()
    generadores = [
        grafico_ventas_por_mes,
        grafico_metodos_pago,
        grafico_navegadores,
        grafico_distribucion_boletin_vale,
        grafico_boletin_vale_por_mes,
        grafico_segmentacion_edad,
        grafico_comparacion_genero,
        grafico_correlacion_edad_venta,
    ]
    return [generador() for generador in generadores]


def main() -> int:
    print("Generando visualizaciones desde Supabase")
    print("=" * 60)
    for ruta in generar_todas():
        print(f"OK  {ruta.relative_to(RAIZ)}")
    print("=" * 60)
    print("OK - visualizaciones generadas correctamente")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

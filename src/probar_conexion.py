"""Diagnostico de la conexion a la base de datos.

Verifica que la cadena de conexion del archivo .env sea alcanzable y explica
la causa cuando no lo es. Nunca imprime la contrasena.

Uso:
    python src/probar_conexion.py
"""

import socket
import sys
from urllib.parse import urlparse

import psycopg

import config


def _partes(url: str):
    """Descompone la URL de conexion sin exponer la contrasena."""
    limpia = url.replace("postgresql+psycopg://", "postgresql://")
    p = urlparse(limpia)
    return p.hostname, p.port or 5432, p.username, (p.path or "/").lstrip("/")


def _consultar(host: str, flags: int = 0) -> tuple[list[str], list[str]]:
    """Resuelve el host y separa las direcciones por familia."""
    ipv4, ipv6 = [], []
    for familia, _, _, _, sockaddr in socket.getaddrinfo(host, None, flags=flags):
        if familia == socket.AF_INET:
            ipv4.append(sockaddr[0])
        elif familia == socket.AF_INET6:
            ipv6.append(sockaddr[0])
    return sorted(set(ipv4)), sorted(set(ipv6))


def revisar_dns(host: str) -> tuple[list[str], list[str], bool]:
    """Devuelve (ipv4, ipv6, solo_visible_con_fallback).

    Sin ruta IPv6, el SO oculta esas direcciones y getaddrinfo falla como si
    el host no existiera. El reintento con AI_ALL|AI_V4MAPPED las revela.
    """
    try:
        ipv4, ipv6 = _consultar(host)
        return ipv4, ipv6, False
    except socket.gaierror:
        ipv4, ipv6 = _consultar(host, flags=socket.AI_ALL | socket.AI_V4MAPPED)
        return ipv4, ipv6, True


def main() -> int:
    print("Diagnostico de conexion a la base de datos")
    print("=" * 60)

    try:
        url = config.obtener_url_bd()
    except RuntimeError as e:
        print(f"ERROR: {e}")
        return 1

    host, puerto, usuario, base = _partes(url)
    print(f"host    : {host}")
    print(f"puerto  : {puerto}")
    print(f"usuario : {usuario}")
    print(f"base    : {base}")
    print("password: (oculta)")
    print("-" * 60)

    # --- 1. Resolucion DNS -------------------------------------------------
    print("[1/3] Resolviendo DNS ...")
    try:
        ipv4, ipv6, oculto = revisar_dns(host)
    except socket.gaierror as e:
        print(f"      FALLA: el host no existe ({e})")
        print("      Revisa que copiaste bien el host desde Supabase.")
        return 1

    print(f"      IPv4: {', '.join(ipv4) if ipv4 else '(ninguna)'}")
    print(f"      IPv6: {', '.join(ipv6) if ipv6 else '(ninguna)'}")

    if not ipv4 and ipv6:
        print()
        print("      PROBLEMA IDENTIFICADO: este host solo publica IPv6.")
        if oculto:
            print("      Ademas, esta maquina no tiene ruta IPv6 hacia internet,")
            print("      por lo que la conexion falla con 'No route to host'.")
        print()
        print("      Es la conexion DIRECTA de Supabase. La solucion es usar el")
        print("      Session pooler, que si publica IPv4 y es gratuito:")
        print("        host   : aws-0-<region>.pooler.supabase.com")
        print(f"        usuario: postgres.<project-ref>   (no '{usuario}')")
        print("        puerto : 5432")
        print()
        print("      Se obtiene en: Supabase -> Connect -> Session pooler")
        return 1

    # --- 2. Conectividad TCP ----------------------------------------------
    print("[2/3] Probando conexion TCP ...")
    try:
        with socket.create_connection((host, puerto), timeout=10):
            print(f"      OK: puerto {puerto} alcanzable")
    except OSError as e:
        print(f"      FALLA: {e}")
        if not ipv4 and ipv6:
            print("      Causa probable: el host es IPv6 y tu red es IPv4.")
        else:
            print("      Revisa tu conexion a internet o un firewall/VPN activa.")
        return 1

    # --- 3. Autenticacion y consulta --------------------------------------
    print("[3/3] Autenticando y consultando ...")
    try:
        with psycopg.connect(
            url.replace("postgresql+psycopg://", "postgresql://"),
            connect_timeout=15,
        ) as con:
            fila = con.execute("SELECT version(), current_database()").fetchone()
            print(f"      OK: {fila[0].split(',')[0]}")
            print(f"      base de datos: {fila[1]}")

            tablas = con.execute(
                """SELECT table_name FROM information_schema.tables
                   WHERE table_schema = 'public' ORDER BY table_name"""
            ).fetchall()
            if tablas:
                print(f"      objetos existentes: {', '.join(t[0] for t in tablas)}")
            else:
                print("      base vacia (aun no se ha ejecutado scripts/modelo.sql)")
    except psycopg.OperationalError as e:
        mensaje = str(e).strip()
        print(f"      FALLA: {mensaje}")
        if "password authentication failed" in mensaje.lower():
            print()
            print("      Con el pooler el usuario debe incluir el project ref:")
            print("        postgres.uvllkkzjiodcddkjjjbs   <- correcto")
            print("        postgres                        <- incorrecto")
            print("      Si la contrasena tiene caracteres especiales (@ : / ?)")
            print("      hay que codificarlos en la URL (percent-encoding).")
        return 1

    print("=" * 60)
    print("CONEXION EXITOSA - listo para ejecutar la carga")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

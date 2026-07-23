"""
main.py
CLI entry point del paquete agente-base.

Uso:
  python -m agente_base --run startups     # Ejecuta agente una vez
  python -m agente_base --daemon           # Loop infinito
  python -m agente_base --list             # Lista agentes disponibles
"""
import sys
import argparse
import logging

from config import CONFIG, setup_logging

setup_logging(CONFIG)
log = logging.getLogger("main")


def listar_agentes():
    import pkgutil
    import importlib

    agentes = importlib.import_module("agentes")
    disponibles = []

    for loader, nombre_mod, is_pkg in pkgutil.iter_modules(agentes.__path__):
        try:
            mod = importlib.import_module(f"agentes.{nombre_mod}")
            for attr_name in dir(mod):
                cls = getattr(mod, attr_name)
                if isinstance(cls, type) and hasattr(cls, "nombre") and cls.__module__ == f"agentes.{nombre_mod}":
                    nombre = cls.nombre
                    intervalo = getattr(cls, "intervalo_horas", "?")
                    temas = getattr(cls, "ntfy_titulo_template", "")
                    disponibles.append((nombre, f"cada {intervalo}h", temas))
        except Exception as e:
            log.warning("Error cargando %s: %s", nombre_mod, e)

    print("\n🤖 Agentes disponibles:\n")
    for nombre, intervalo, temas in sorted(disponibles):
        print(f"  {nombre:<20} {intervalo:<10} {temas}")
    print()


def main():
    parser = argparse.ArgumentParser(description="agente-base: motor de agentes AI")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--run", type=str, metavar="AGENTE", help="Ejecutar un agente una vez")
    grupo.add_argument("--daemon", action="store_true", help="Modo daemon: ejecuta agentes en loop")
    grupo.add_argument("--list", action="store_true", help="Listar agentes disponibles")

    args = parser.parse_args()

    if args.list:
        listar_agentes()

    elif args.run:
        nombre = args.run
        log.info("Ejecutando agente: %s", nombre)
        from scheduler import ejecutar_una_vez
        try:
            enviado, cantidad = ejecutar_una_vez(nombre)
            log.info("Resultado: %d items procesados, enviado=%s", cantidad, enviado)
        except Exception as e:
            log.exception("Error: %s", e)
            sys.exit(1)

    elif args.daemon:
        log.info("Modo daemon activado")
        from scheduler import daemon
        daemon()


if __name__ == "__main__":
    main()

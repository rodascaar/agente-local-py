"""
scheduler.py
Cron-like interno para ejecutar agentes en bucle.

Soporta:
- scheduled_times: lista de "HH:MM" (ej. ["09:00", "21:00"])
  El agente corre solo en esos horarios, con ventana de tolerancia.
- spacing_entre_agentes: pausa entre un agente y el siguiente
  para no saturar el LLM.
- Fallback a intervalo_horas si scheduled_times es None.
"""
import time
import logging
from datetime import datetime

from config import CONFIG

log = logging.getLogger("scheduler")


def instanciar_agente(nombre):
    import importlib

    mod = importlib.import_module(f"agentes.{nombre}")
    for attr_name in dir(mod):
        cls = getattr(mod, attr_name)
        if isinstance(cls, type) and hasattr(cls, "nombre") and cls.nombre == nombre and cls.__module__ == f"agentes.{nombre}":
            return cls()
    raise ValueError(f"No se encontró clase para agente '{nombre}' en agentes.{nombre}")


def ejecutar_una_vez(nombre):
    agente = instanciar_agente(nombre)
    return agente.ejecutar()


def _descubrir_agentes():
    import importlib
    import pkgutil

    agentes_pkg = importlib.import_module("agentes")
    instancias = []
    for _, nombre_mod, _ in pkgutil.iter_modules(agentes_pkg.__path__):
        try:
            mod = importlib.import_module(f"agentes.{nombre_mod}")
            for attr_name in dir(mod):
                cls = getattr(mod, attr_name)
                if isinstance(cls, type) and hasattr(cls, "nombre") and cls.__module__ == f"agentes.{nombre_mod}":
                    instancias.append(cls())
        except Exception as e:
            log.warning("Error descubriendo %s: %s", nombre_mod, e)
    return instancias


def _debe_ejecutar(agente, ultima_ejecucion):
    """Determina si un agente debe ejecutarse ahora."""
    nombre = agente.nombre
    ultima = ultima_ejecucion.get(nombre, 0.0)
    ahora = time.time()
    ahora_dt = datetime.now()

    if not agente.scheduled_times:
        ultima = ultima_ejecucion.get(nombre, 0)
        return ahora - ultima >= agente.intervalo_horas * 3600

    ventana_min = CONFIG["scheduler"].get("ventana_horaria_minutos", 120)

    for st in agente.scheduled_times:
        try:
            h, m = map(int, st.split(":"))
        except Exception:
            log.warning("scheduled_time inválido '%s' en %s", st, nombre)
            continue

        sched_dt = ahora_dt.replace(hour=h, minute=m, second=0, microsecond=0)
        sched_ts = sched_dt.timestamp()

        diff = ahora - sched_ts
        if diff >= 0 and diff < ventana_min * 60 and ultima < sched_ts:
            return True

    return False


def daemon():
    check_interval = CONFIG["scheduler"]["check_interval_segundos"]
    spacing = CONFIG["scheduler"].get("spacing_entre_agentes", 300)

    log.info("Scheduler daemon iniciado (check cada %ds, spacing %ds)", check_interval, spacing)

    ultima_ejecucion = {}

    while True:
        agentes = _descubrir_agentes()

        # ordenar por scheduled_times para respetar el orden del día
        agentes.sort(key=lambda a: a.scheduled_times[0] if a.scheduled_times else "99:99")

        for agente in agentes:
            if not _debe_ejecutar(agente, ultima_ejecucion):
                continue

            nombre = agente.nombre
            log.info("[daemon] Ejecutando %s...", nombre)
            try:
                enviado, cantidad = agente.ejecutar()
                log.info("[daemon] %s terminó: %d items, enviado=%s", nombre, cantidad, enviado)
            except Exception as e:
                log.exception("[daemon] Error en %s: %s", nombre, e)

            ultima_ejecucion[nombre] = time.time()

            log.info("[daemon] Spacing %ds antes del próximo agente...", spacing)
            time.sleep(spacing)

        time.sleep(check_interval)

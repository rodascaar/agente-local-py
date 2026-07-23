"""
ntfy.py
Envío de notificaciones push vía ntfy.sh, con reintentos.

Topic configurable por agente (default del config global).
"""
import time
import logging
import requests

from config import CONFIG

log = logging.getLogger("ntfy")


def enviar(mensaje, titulo="", topic=None, tags="robot", priority="default", reintentos=2):
    cfg = CONFIG["ntfy"]
    topic = topic or cfg["default_topic"]
    timeout = cfg.get("timeout", 10)
    url = f"https://ntfy.sh/{topic}"

    for intento in range(1, reintentos + 1):
        try:
            r = requests.post(
                url,
                data=mensaje.encode("utf-8"),
                headers={
                    "Title": titulo.encode("utf-8"),
                    "Markdown": "yes",
                    "Priority": priority,
                    "Tags": tags,
                },
                timeout=timeout,
            )
            if r.ok:
                log.info("ntfy enviado a %s (intento %d)", topic, intento)
                return True
            log.warning("ntfy HTTP %d (intento %d)", r.status_code, intento)
        except Exception as e:
            log.warning("ntfy error (intento %d): %s", intento, e)
        time.sleep(2 * intento)

    log.error("ntfy falló definitivamente a %s", topic)
    return False

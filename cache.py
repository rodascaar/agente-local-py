"""
cache.py
Cache persistente de items vistos, dict-based y thread-safe.

Un archivo JSON por agente: cache/<nombre_agente>.json
Migración automática si estaba en formato lista (compat con agentes viejos).
"""
import os
import json
import logging
import threading
from datetime import datetime

log = logging.getLogger("cache")

_lock = threading.Lock()


class Cache:
    def __init__(self, nombre, cache_dir=None):
        from config import CONFIG

        self.cache_dir = cache_dir or CONFIG["cache"]["dir"]
        os.makedirs(self.cache_dir, exist_ok=True)
        self.path = os.path.join(self.cache_dir, f"{nombre}.json")
        self._data = {}
        self._cargar()

    def _cargar(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                log.info("Migrando cache de lista a dict (%d items).", len(data))
                self._data = {eid: {"estado": "visto", "fecha": ""} for eid in data}
                self._guardar()
            else:
                self._data = data
        except Exception as e:
            log.warning("Error leyendo cache %s: %s. Empiezo vacío.", self.path, e)
            self._data = {}

    def _guardar(self):
        with _lock:
            try:
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, ensure_ascii=False)
            except Exception as e:
                log.error("Error guardando cache %s: %s", self.path, e)

    def visto(self, eid):
        return eid in self._data

    def marcar(self, eid, estado="enviado", **extra):
        with _lock:
            self._data[eid] = {"estado": estado, "fecha": datetime.now().isoformat(), **extra}
    def __len__(self):
        return len(self._data)

    def __contains__(self, eid):
        return eid in self._data

    def guardar(self):
        self._guardar()

    def resetear(self):
        with _lock:
            self._data = {}
        self._guardar()
        log.info("Cache reseteado: %s", self.path)

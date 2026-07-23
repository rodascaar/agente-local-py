"""
config.py
Configuración central del paquete agente-base.

Leé config.json si existe (override), si no, usa defaults con auto-detección.
"""
import os
import json
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(BASE_DIR, "cache")
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def _defaults():
    return {
        "llm": {
            "ollama_url": "http://127.0.0.1:11434",
            "ollama_model": "qwen2.5:3b",
            "timeout": 300,
            "default_options": {
                "num_predict": 200,
                "temperature": 0.5,
                "num_ctx": 2048,
            },
        },
        "ntfy": {
            "default_topic": "agente-local-py-default",
            "timeout": 10,
        },
        "cache": {
            "dir": CACHE_DIR,
        },
        "scheduler": {
            "check_interval_segundos": 60,
            "reintentos_llm_segundos": 300,
            "spacing_entre_agentes": 300,
            "ventana_horaria_minutos": 120,
        },
        "logging": {
            "level": "INFO",
            "file": None,
        },
    }


def cargar_config():
    cfg = _defaults()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                override = json.load(f)
            _merge(cfg, override)
        except Exception as e:
            logging.warning("No pude leer config.json (%s). Uso defaults.", e)
    return cfg


def _merge(base, override):
    for k, v in override.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _merge(base[k], v)
        else:
            base[k] = v


def setup_logging(cfg):
    level_name = cfg.get("logging", {}).get("level", "INFO")
    level = getattr(logging, level_name.upper(), logging.INFO)
    log_file = cfg.get("logging", {}).get("file")
    handlers = [logging.StreamHandler()]
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
    logging.basicConfig(level=level, format=LOG_FORMAT, handlers=handlers, force=True)


CONFIG = cargar_config()

"""
llm.py
Unifica llama.cpp (llama-server, API OpenAI-compatible en :8080) y Ollama (:11434).

- Backend "auto": detecta cuál está disponible, prefiere llama.cpp.
- Backend "llama" o "ollama": fuerza uno.
- Fallback: si el primario falla, prueba el secundario automáticamente.
- Sólo un backend al mismo tiempo — nunca se cargan dos modelos en paralelo.
"""
import time
import logging
import requests

from config import CONFIG

log = logging.getLogger("llm")


class LLM:
    def __init__(self, cfg=None):
        self.cfg = cfg or CONFIG["llm"]
        self.timeout = self.cfg.get("timeout", 180)
        self.backend = None
        self._probar_backends()

    def _probar_backends(self):
        modo = self.cfg.get("backend", "auto")
        if modo == "llama":
            if self._ping("llama"):
                self.backend = "llama"
            else:
                log.warning("Config dice 'llama' pero no responde. Intento ollama.")
                if self._ping("ollama"):
                    self.backend = "ollama"
        elif modo == "ollama":
            if self._ping("ollama"):
                self.backend = "ollama"
            else:
                log.warning("Config dice 'ollama' pero no responde. Intento llama.")
                if self._ping("llama"):
                    self.backend = "llama"
        else:
            if self._ping("llama"):
                self.backend = "llama"
            elif self._ping("ollama"):
                self.backend = "ollama"

        if self.backend:
            log.info("Backend LLM activo: %s", self.backend)
        else:
            log.error("Ningún backend LLM disponible (ni llama.cpp ni ollama).")

    def _ping(self, nombre):
        if nombre == "llama":
            url = self.cfg["llama_url"].rstrip("/") + "/health"
        else:
            url = self.cfg["ollama_url"].rstrip("/") + "/api/tags"
        try:
            r = requests.get(url, timeout=5)
            return r.ok
        except Exception:
            return False

    def _llama_chat(self, system_prompt, user_msg, options=None):
        url = self.cfg["llama_url"].rstrip("/") + "/v1/chat/completions"
        opts = dict(self.cfg.get("default_options", {}))
        if options:
            opts.update(options)
        body = {
            "model": self.cfg.get("llama_model", "gemma4-e2b"),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            "temperature": opts.get("temperature", 0.5),
            "max_tokens": opts.get("num_predict", 200),
            "stream": False,
        }
        r = requests.post(url, json=body, timeout=self.timeout)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    def _ollama_chat(self, system_prompt, user_msg, options=None):
        url = self.cfg["ollama_url"].rstrip("/") + "/api/chat"
        opts = dict(self.cfg.get("default_options", {}))
        if options:
            opts.update(options)
        body = {
            "model": self.cfg.get("ollama_model", "qwen2.5:1.5b"),
            "stream": False,
            "keep_alive": "5m",
            "options": opts,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
        }
        r = requests.post(url, json=body, timeout=self.timeout)
        r.raise_for_status()
        return r.json()["message"]["content"].strip()

    def _chat(self, system_prompt, user_msg, options=None, backend=None):
        backend = backend or self.backend
        if backend == "llama":
            return self._llama_chat(system_prompt, user_msg, options)
        elif backend == "ollama":
            return self._ollama_chat(system_prompt, user_msg, options)
        raise RuntimeError("No hay backend LLM activo.")

    def resumir(self, system_prompt, user_msg, options=None):
        if not self.backend:
            self._probar_backends()
        if not self.backend:
            log.error("Sin backend. ¿Está corriendo llama-server u ollama?")
            return None

        primario = self.backend
        try:
            return self._chat(system_prompt, user_msg, options, backend=primario)
        except Exception as e:
            log.warning("Backend '%s' falló (%s). Probando fallback...", primario, e)

        fallback = "ollama" if primario == "llama" else "llama"
        if self._ping(fallback):
            try:
                log.info("Fallback activo: %s", fallback)
                texto = self._chat(system_prompt, user_msg, options, backend=fallback)
                self.backend = fallback
                return texto
            except Exception as e:
                log.error("Fallback '%s' también falló: %s", fallback, e)
        else:
            log.error("Fallback '%s' no disponible.", fallback)
        return None

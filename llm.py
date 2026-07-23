"""
llm.py
Unifica llama.cpp (llama-server, :8080) y Ollama (:11434).

Detección de API:
  - Intenta /v1/chat/completions (OpenAI, moderno)
  - Si da 400: mergea system prompt en user message (modelos sin role system)
  - Si da 400 igual: usa /completion legacy con prompt formateado
  - El formato detectado se cachea para evitar re-detección

Auto-start:
  - Si config tiene start_command y auto_start=true, lanza llama-server
    automáticamente cuando no está corriendo.
"""
import time
import logging
import subprocess
import requests

from config import CONFIG

log = logging.getLogger("llm")


class LLM:
    def __init__(self, cfg=None):
        self.cfg = cfg or CONFIG["llm"]
        self.timeout = self.cfg.get("timeout", 180)
        self.backend = None
        self.llama_api = None
        self._probar_backends()

    # ── detección de backends ─────────────────────────────────

    def _probar_backends(self):
        modo = self.cfg.get("backend", "auto")
        if modo == "llama":
            if self._ping("llama"):
                self.backend = "llama"
            else:
                self._auto_start()
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
                    self._auto_start()
                    if self._ping("llama"):
                        self.backend = "llama"
        else:
            if self._ping("llama"):
                self.backend = "llama"
            elif self._ping("ollama"):
                self.backend = "ollama"
            else:
                self._auto_start()
                if self._ping("llama"):
                    self.backend = "llama"
                elif self._ping("ollama"):
                    self.backend = "ollama"

        if self.backend:
            log.info("Backend LLM activo: %s (api=%s)", self.backend, self.llama_api)
        else:
            log.error("Ningún backend LLM disponible.")

    def _ping(self, nombre):
        if nombre == "llama":
            return self._ping_llama()
        else:
            return self._ping_ollama()

    def _ping_llama(self):
        url = self.cfg["llama_url"].rstrip("/") + "/health"
        try:
            r = requests.get(url, timeout=5)
            if not r.ok:
                return False
        except Exception:
            return False

        self.llama_api = self._detect_llama_api()
        return self.llama_api is not None

    def _ping_ollama(self):
        url = self.cfg["ollama_url"].rstrip("/") + "/api/tags"
        try:
            r = requests.get(url, timeout=5)
            return r.ok
        except Exception:
            return False

    def _detect_llama_api(self):
        base = self.cfg["llama_url"].rstrip("/")
        test_msg = [{"role": "user", "content": "hi"}]

        tries = [
            ("openai", f"{base}/v1/chat/completions", {"messages": test_msg, "max_tokens": 1, "stream": False}),
            ("openai_nosys", f"{base}/v1/chat/completions", {"messages": test_msg, "max_tokens": 1, "stream": False}),
            ("legacy", f"{base}/completion", {"prompt": "hi", "n_predict": 1, "stream": False}),
        ]

        for api_name, endpoint, body in tries:
            try:
                r = requests.post(endpoint, json=body, timeout=5)
                if r.ok or r.status_code == 400:
                    log.info("llama.cpp API detectada: %s (%s)", api_name, endpoint)
                    return api_name
            except Exception:
                continue

        log.warning("No se pudo detectar API de llama.cpp")
        return None

    def _auto_start(self):
        if not self.cfg.get("auto_start"):
            return
        cmd = self.cfg.get("start_command", "").strip()
        if not cmd:
            return
        log.info("Auto-start: ejecutando %s ...", cmd)
        try:
            subprocess.Popen(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            timeout = self.cfg.get("start_timeout", 30)
            for _ in range(timeout):
                time.sleep(1)
                if self._ping_llama():
                    log.info("Auto-start: llama.cpp levantado correctamente")
                    return
            log.warning("Auto-start: llama.cpp no respondió después de %ds", timeout)
        except Exception as e:
            log.error("Auto-start: error al ejecutar '%s': %s", cmd, e)

    # ── llamadas al LLM ───────────────────────────────────────

    def _llama_chat(self, system_prompt, user_msg, options=None):
        base = self.cfg["llama_url"].rstrip("/")
        opts = dict(self.cfg.get("default_options", {}))
        if options:
            opts.update(options)

        api = self.llama_api or "openai"

        if api == "openai" or api == "openai_nosys":
            endpoint = f"{base}/v1/chat/completions"
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ]
            if api == "openai_nosys":
                messages = [
                    {"role": "user", "content": f"{system_prompt}\n\n{user_msg}"},
                ]

            body = {
                "model": self.cfg.get("llama_model", "gemma4-e2b"),
                "messages": messages,
                "temperature": opts.get("temperature", 0.5),
                "max_tokens": opts.get("num_predict", 200),
                "stream": False,
            }
            r = requests.post(endpoint, json=body, timeout=self.timeout)
            if not r.ok and r.status_code == 400 and api == "openai":
                log.warning("llama.cpp rechazó role system. Reintento sin system...")
                self.llama_api = "openai_nosys"
                return self._llama_chat(system_prompt, user_msg, options)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()

        else:
            endpoint = f"{base}/completion"
            prompt = f"System: {system_prompt}\n\nUser: {user_msg}\n\nAssistant:"
            body = {
                "prompt": prompt,
                "n_predict": opts.get("num_predict", 200),
                "temperature": opts.get("temperature", 0.5),
                "stream": False,
            }
            r = requests.post(endpoint, json=body, timeout=self.timeout)
            r.raise_for_status()
            return r.json()["content"].strip()

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

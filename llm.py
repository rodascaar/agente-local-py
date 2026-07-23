"""
llm.py
Unifica llama.cpp (llama-server, :8080) y Ollama (:11434).

Cada request intenta SIEMPRE llama.cpp primero:
  1. Ping a /health de llama.cpp
  2. Si responde: _llama_chat() con API detectada (openai / openai_nosys / legacy)
  3. Si no responde y auto_start=true: ejecuta start_command, espera, reintenta
  4. Si no hay forma: cae en Ollama

No cachea backend fijo. Cada resumir() evalúa.
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
        self.llama_api = None

    def _health_llama(self):
        """GET /health rápido. No detecta API."""
        url = self.cfg["llama_url"].rstrip("/") + "/health"
        try:
            r = requests.get(url, timeout=2)
            return r.ok
        except Exception:
            return False

    def _ping_llama(self):
        """Health + detección de API."""
        if not self._health_llama():
            return False
        api = self._detect_llama_api()
        if api:
            self.llama_api = api
            return True
        return False

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
                r = requests.post(endpoint, json=body, timeout=15)
                if r.ok or r.status_code == 400:
                    log.info("llama.cpp API detectada: %s", api_name)
                    return api_name
            except Exception:
                continue
        return None

    def _auto_start(self):
        cmd = self.cfg.get("start_command", "").strip()
        if not cmd:
            log.warning("auto_start=true pero start_command vacío")
            return
        log.info("Auto-start: %s ...", cmd)
        try:
            proc = subprocess.Popen(
                cmd, shell=True, start_new_session=True,
                stdin=subprocess.DEVNULL,
            )
            timeout = self.cfg.get("start_timeout", 30)
            for _ in range(timeout):
                time.sleep(1)
                if self._health_llama():
                    log.info("llama-server escuchando, cargando modelo...")
                    break
            else:
                proc.poll()
                log.warning("no respondió tras %ds", timeout)
                return

            base = self.cfg["llama_url"].rstrip("/")
            warmup = {
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1, "stream": False,
            }
            warmup_timeout = self.cfg.get("warmup_timeout", 180)
            try:
                requests.post(f"{base}/v1/chat/completions", json=warmup, timeout=warmup_timeout)
                log.info("Modelo cargado")
            except requests.exceptions.ReadTimeout:
                log.warning("Warmup agotó %ds", warmup_timeout)
            except Exception as e:
                log.warning("Warmup falló: %s", e)

            proc.poll()
        except Exception as e:
            log.error("auto-start error: %s", e)

    def _llama_chat(self, system_prompt, user_msg, options=None):
        base = self.cfg["llama_url"].rstrip("/")
        opts = dict(self.cfg.get("default_options", {}))
        if options:
            opts.update(options)
        api = self.llama_api or "openai"

        if api in ("openai", "openai_nosys"):
            endpoint = f"{base}/v1/chat/completions"
            if api == "openai":
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_msg},
                ]
            else:
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

    def resumir(self, system_prompt, user_msg, options=None):
        # 1. Intentar llama.cpp siempre primero
        if self._health_llama():
            if not self.llama_api:
                self._detect_llama_api()
            try:
                log.info("Usando llama.cpp")
                return self._llama_chat(system_prompt, user_msg, options)
            except Exception as e:
                log.warning("llama.cpp falló: %s. Probando Ollama...", e)
        else:
            if self.cfg.get("auto_start"):
                log.info("llama.cpp caído. Intentando auto-start...")
                self._auto_start()
                if self._health_llama():
                    if not self.llama_api:
                        self._detect_llama_api()
                    try:
                        log.info("Usando llama.cpp (tras auto-start)")
                        return self._llama_chat(system_prompt, user_msg, options)
                    except Exception as e:
                        log.warning("llama.cpp falló tras auto-start: %s", e)

        # 2. Fallback a Ollama
        if self._ping_ollama():
            try:
                log.info("Usando Ollama (fallback)")
                return self._ollama_chat(system_prompt, user_msg, options)
            except Exception as e:
                log.error("Ollama también falló: %s", e)
        else:
            log.error("Ollama no disponible")

        log.error("Ningún backend pudo procesar el request")
        return None

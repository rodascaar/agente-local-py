import logging
import requests

from config import CONFIG

log = logging.getLogger("llm")


class LLM:
    def __init__(self, cfg=None):
        self.cfg = cfg or CONFIG["llm"]
        self.timeout = self.cfg.get("timeout", 180)

    def resumir(self, system_prompt, user_msg, options=None):
        url = self.cfg["ollama_url"].rstrip("/") + "/api/chat"
        opts = dict(self.cfg.get("default_options", {}))
        if options:
            opts.update(options)
        body = {
            "model": self.cfg.get("ollama_model", "qwen2.5:3b"),
            "stream": False,
            "keep_alive": "5m",
            "options": opts,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
        }
        log.info("Usando Ollama (%s)", body["model"])
        try:
            r = requests.post(url, json=body, timeout=self.timeout)
            r.raise_for_status()
            return r.json()["message"]["content"].strip()
        except Exception as e:
            log.error("Ollama falló: %s", e)
            return None

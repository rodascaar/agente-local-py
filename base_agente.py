"""
base_agente.py
Clase base abstracta que todos los agentes heredan.

Chunking automático: si los items no entran en el contexto del LLM
(num_ctx), se parten en chunks. Cada chunk se resume por separado
y luego se mergean en un solo informe final.

Flujo:
1. Parsea feeds, filtra, descarta cacheados
2. Si hay items, mide si entran en ctx
3. Si no entran: parte en chunks → LLM por chunk → merge
4. Si entran: LLM directo (una sola llamada)
5. Arma reporte final, ntfy, marca cache
"""
import logging
from abc import ABC, abstractmethod
from datetime import datetime

import feeds as feeds_mod
import cache as cache_mod
import ntfy
from llm import LLM
from config import CONFIG

log = logging.getLogger("agente")


class AgenteBase(ABC):
    nombre = "base"
    intervalo_horas = 24
    scheduled_times = None
    max_items_por_feed = 20
    max_items_totales = 30
    max_chars_por_item = 500
    ntfy_topic = None
    ntfy_tags = "robot"
    ntfy_titulo_template = "Agente: {nombre} — {fecha}"
    horas_recientes = 24
    feeds = []

    def __init__(self):
        self.cache = cache_mod.Cache(self.nombre)
        self.llm = LLM()

    def filtrar(self, item):
        return False

    @abstractmethod
    def system_prompt(self):
        ...

    def construir_user_msg(self, items):
        out = []
        for i, it in enumerate(items, 1):
            out.append(f"--- ITEM {i} ({it.fuente}) ---")
            out.append(f"Título: {it.titulo}")
            fragmento = feeds_mod.extraer_fragmento(it.cuerpo, self.max_chars_por_item)
            out.append(f"Resumen: {fragmento}")
            out.append("")
        return "\n".join(out)

    def generar_reporte(self, items, resumen_llm):
        if resumen_llm is None:
            return None
        sep = "─────────────────"
        cuerpo = [resumen_llm, sep]
        for it in items[:10]:
            cuerpo.append(f"[{it.fuente}] {it.titulo}")
            cuerpo.append(f"🔗 {it.link}")
        cuerpo.append(sep)
        return "\n".join(cuerpo)

    def opciones_llm(self):
        return None

    def chunk_merge_prompt(self):
        return (
            "Te paso varios resúmenes parciales generados a partir de distintas fuentes. "
            "Combiná todo en un solo informe coherente. Eliminá duplicados, "
            "ordená por importancia, unificá el tono. "
            "Usá voseo argentino. Máximo 5 puntos finales."
        )

    # ── chunking interno ──────────────────────────────────────

    def _ctx_budget(self):
        opts = self.opciones_llm() or {}
        num_ctx = opts.get("num_ctx", CONFIG.get("llm", {}).get("default_options", {}).get("num_ctx", 4096))
        sys_prompt = self.system_prompt()
        sys_tokens = len(sys_prompt) // 3
        output_reserve = 500
        return num_ctx - sys_tokens - output_reserve - 100

    def _estimar_tokens_item(self, item):
        titulo = len(f"Título: {item.titulo}\n") // 3
        cuerpo = len(f"Resumen: {feeds_mod.extraer_fragmento(item.cuerpo, self.max_chars_por_item)}\n") // 3
        overhead = len(f"--- ITEM N ({item.fuente}) ---\n\n") // 3
        return 1 + titulo + cuerpo + overhead

    def _chunkear(self, items, budget):
        chunks = []
        current = []
        current_tok = 0
        for it in items:
            tok = self._estimar_tokens_item(it)
            if current_tok + tok > budget and current:
                chunks.append(current)
                current = []
                current_tok = 0
            current.append(it)
            current_tok += tok
        if current:
            chunks.append(current)
        return chunks

    def _merge_resumenes(self, resumenes):
        if len(resumenes) == 1:
            return resumenes[0]
        msg = "\n\n--- SIGUIENTE LOTE ---\n\n".join(resumenes)
        try:
            merged = self.llm.resumir(self.chunk_merge_prompt(), msg, options={"num_predict": 800, "num_ctx": 2048})
            return merged or "\n\n".join(resumenes)
        except Exception:
            return "\n\n".join(resumenes)

    # ── ciclo principal ──────────────────────────────────────

    def ejecutar(self):
        log.info("[%s] iniciando ciclo", self.nombre)
        nuevos = []

        for feed_cfg in self.feeds:
            if isinstance(feed_cfg, tuple):
                if len(feed_cfg) == 2:
                    fnombre, url = feed_cfg
                    headers = None
                else:
                    fnombre, url, headers = feed_cfg
            else:
                url = feed_cfg
                fnombre = feed_cfg

            try:
                items = feeds_mod.parsear_feed(
                    url, nombre=fnombre, headers=headers,
                    max_items=self.max_items_por_feed, horas=self.horas_recientes,
                )
                log.info("[%s] %s: %d items crudos", self.nombre, fnombre, len(items))
            except Exception as e:
                log.error("[%s] error en feed %s: %s", self.nombre, fnombre, e)
                continue

            for it in items:
                if it.id in self.cache:
                    continue
                if self.filtrar(it):
                    self.cache.marcar(it.id, estado="filtrado")
                    continue
                nuevos.append(it)
            if len(nuevos) >= self.max_items_totales:
                break

        if not nuevos:
            log.info("[%s] sin novedades. Todo al día.", self.nombre)
            self.cache.guardar()
            return False, 0

        budget = self._ctx_budget()
        chunks = self._chunkear(nuevos, budget)
        log.info("[%s] %d items en %d chunks (budget %d tok)", self.nombre, len(nuevos), len(chunks), budget)

        resumenes = []
        for i, chunk in enumerate(chunks):
            log.info("[%s] chunk %d/%d: %d items", self.nombre, i + 1, len(chunks), len(chunk))
            msg = self.construir_user_msg(chunk)
            r = self.llm.resumir(self.system_prompt(), msg, options=self.opciones_llm())
            if r:
                resumenes.append(r)

        if not resumenes:
            log.error("[%s] LLM no pudo generar ningún resumen. Postergo.", self.nombre)
            self.cache.guardar()
            return False, len(nuevos)

        resumen_final = self._merge_resumenes(resumenes)
        txt = self.generar_reporte(nuevos, resumen_final)
        if not txt:
            self.cache.guardar()
            return False, len(nuevos)

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        titulo = self.ntfy_titulo_template.format(nombre=self.nombre, fecha=fecha)
        enviado = ntfy.enviar(txt, titulo=titulo, topic=self.ntfy_topic, tags=self.ntfy_tags)

        for it in nuevos:
            self.cache.marcar(it.id, estado="enviado", titulo=it.titulo, link=it.link)
        self.cache.guardar()

        log.info("[%s] ciclo OK. %d items, %d chunks, enviado=%s", self.nombre, len(nuevos), len(chunks), enviado)
        return enviado, len(nuevos)

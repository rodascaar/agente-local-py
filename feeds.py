"""
feeds.py
Parser de feeds RSS/Atom con tolerancia a feeds malformed.

- Usa feedparser como primario.
- Si bozo=True y 0 entries, intenta fetch manual + regex fallback (IndieHackers, HN Show).
- Headers personalizables (User-Agent para Reddit).
- Filtrado por antigüedad (24h por defecto, configurable).
"""
import re
import time
import logging
from datetime import datetime, timedelta

import feedparser
import requests

log = logging.getLogger("feeds")

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
DEFAULT_HEADERS = {"User-Agent": UA, "Accept": "application/rss+xml, application/atom+xml, text/html"}


class Item:
    __slots__ = ("titulo", "cuerpo", "link", "fuente", "id", "fecha")

    def __init__(self, titulo, cuerpo, link, fuente, id, fecha=None):
        self.titulo = titulo
        self.cuerpo = cuerpo
        self.link = link
        self.fuente = fuente
        self.id = id
        self.fecha = fecha

    def __repr__(self):
        return f"<Item [{self.fuente}] {self.titulo[:50]}>"


def limpiar_html(texto_html):
    if not texto_html:
        return ""
    t = re.sub(r"<[^>]+>", "", texto_html)
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def extraer_fragmento(texto, max_chars=500):
    if not texto:
        return ""
    if len(texto) <= max_chars:
        return texto
    return texto[:max_chars].rsplit(" ", 1)[0] + "..."


def _es_reciente(entry, horas=24):
    try:
        if getattr(entry, "published_parsed", None):
            pub = datetime(*entry.published_parsed[:6])
            return (datetime.now() - pub).total_seconds() < horas * 3600
        if getattr(entry, "updated_parsed", None):
            pub = datetime(*entry.updated_parsed[:6])
            return (datetime.now() - pub).total_seconds() < horas * 3600
    except Exception:
        pass
    return True


def _fallback_regex(url, nombre, headers=None):
    """Fetch manual + regex cuando feedparser no puede parsear el feed."""
    try:
        h = headers or DEFAULT_HEADERS
        r = requests.get(url, headers=h, timeout=15)
        r.raise_for_status()
        xml = r.text
    except Exception as e:
        log.warning("Fallback fetch falló (%s): %s", url, e)
        return []

    items = []
    for m in re.finditer(r"<item[^>]*>(.*?)</item>", xml, re.DOTALL | re.IGNORECASE):
        block = m.group(1)
        tm = re.search(r"<title>(.*?)</title>", block, re.DOTALL | re.IGNORECASE)
        lm = re.search(r"<link>(.*?)</link>", block, re.DOTALL | re.IGNORECASE)
        um = re.search(r"<description>(.*?)</description>", block, re.DOTALL | re.IGNORECASE)
        if tm:
            titulo = tm.group(1).strip()
            titulo = re.sub(r"<!\[CDATA\[|\]\]>", "", titulo)
            link = lm.group(1).strip() if lm else ""
            cuerpo = ""
            if um:
                cuerpo = limpiar_html(um.group(1))
            items.append(Item(titulo, cuerpo, link, nombre, link or titulo))
    return items


def parsear_feed(url, nombre=None, headers=None, max_items=20, horas=24):
    """Devuelve lista de Item, filtrando por antigüedad y cap."""

    if not nombre:
        nombre = url

    opts = {}
    if headers:
        opts["request_headers"] = headers

    feed = feedparser.parse(url, **opts)

    if feed.bozo and not feed.entries:
        log.warning("Feed malformed (%s): %s. Intento fallback regex.", url, feed.bozo_exception)
        return _fallback_regex(url, nombre, headers)

    if not feed.entries:
        log.info("Feed vacío: %s", url)
        return []

    items = []
    for e in feed.entries:
        if len(items) >= max_items:
            break
        if not horas or _es_reciente(e, horas):
            eid = e.get("id", e.get("link", e.get("title", str(id(e)))))
            raw = ""
            if "content" in e:
                raw = e.content[0].value
            elif "summary" in e:
                raw = e.summary
            elif "description" in e:
                raw = e.description
            cuerpo = limpiar_html(raw)
            titulo = getattr(e, "title", "")
            link = getattr(e, "link", "")
            items.append(Item(titulo, cuerpo, link, nombre, eid))
    return items

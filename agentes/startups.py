"""
startups.py
Radar de Oportunidades de Negocio.

Monitorea Product Hunt, HN, Reddit, IndieHackers, etc.
Detecta problemas recurrentes, posibles MVPs para Paraguay/LATAM y nichos con poca competencia.
Migrado desde radar_oportunidades.py
"""
from base_agente import AgenteBase

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

PALABRAS_NEGATIVO = [
    "hiring", "job", "career", "salary", "insurance",
    "crypto scam", "nft drop", "airdrop",
]

PALABRAS_PROBLEMA = [
    "problem", "issue", "frustrated", "pain", "need", "wish",
    "i hate", "i want", "i need", "looking for", "is there a tool",
    "why is there no", "someone should build", "i would pay for",
    "i'd pay for", "paying for", "expensive", "too expensive",
    "clunky", "broken", "annoying", "tedious", "manual",
    "no good tool", "no tool", "missing", "gap", "opportunity",
    "underserved", "no one is building", "monopoly", "no competition",
    "alternatives to", "cheaper than", "open source alternative",
]

PALABRAS_PARAGUAY = [
    "paraguay", "latam", "latin america", "latinoamerica",
    "spanish", "español", "argentina", "brazil", "brasil",
    "emerging market", "mercado emergente", "pyme", "msme",
    "small business", "fintech", "payments", "pagos",
    "bancarizacion", "unbanked", "whatsapp", "telegram",
    "local", "regional", "informal economy", "economia informal",
]


class StartupsAgent(AgenteBase):
    nombre = "startups"
    intervalo_horas = 24
    scheduled_times = ["09:00"]
    max_items_por_feed = 15
    max_items_totales = 40
    ntfy_topic = "agente-local-py-oportunidades"
    ntfy_tags = "money,rocket"
    ntfy_titulo_template = "🎯 Radar de Oportunidades — {fecha}"

    feeds = [
        ("Product Hunt", "https://www.producthunt.com/feed"),
        ("Product Hunt - AI", "https://www.producthunt.com/feed?category=artificial-intelligence"),
        ("Product Hunt - SaaS", "https://www.producthunt.com/feed?category=saas"),
        ("Product Hunt - DevTools", "https://www.producthunt.com/feed?category=developer-tools"),
        ("Product Hunt - Fintech", "https://www.producthunt.com/feed?category=finance-fintech"),
        ("Product Hunt - Productivity", "https://www.producthunt.com/feed?category=productivity"),
        ("HN Frontpage", "https://news.ycombinator.com/rss"),
        ("HN Show", "https://news.ycombinator.com/showrss"),
        ("IndieHackers (Medium)", "https://medium.com/feed/indiehackers"),
        ("Saastr", "https://www.saastr.com/feed/"),
        ("Techmeme", "https://www.techmeme.com/feed.xml"),
        ("Reddit SaaS", "https://www.reddit.com/r/SaaS/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("Reddit Entrepreneur", "https://www.reddit.com/r/Entrepreneur/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("Reddit Startups", "https://www.reddit.com/r/startups/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("Reddit SmallBiz", "https://www.reddit.com/r/smallbusiness/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("Reddit IndieHackers", "https://www.reddit.com/r/indiehackers/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("Reddit Bootstrapped", "https://www.reddit.com/r/Bootstrapped/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("Reddit MicroSaaS", "https://www.reddit.com/r/MicroSaaS/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("Reddit SideProject", "https://www.reddit.com/r/sideproject/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("Reddit NoCode", "https://www.reddit.com/r/nocode/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
    ]

    def filtrar(self, item):
        texto = f"{item.titulo} {item.cuerpo}".lower()
        if any(p in texto for p in PALABRAS_NEGATIVO):
            return True
        if "product hunt" in item.fuente.lower():
            return False
        return not (
            any(p in texto for p in PALABRAS_PROBLEMA)
            or any(p in texto for p in PALABRAS_PARAGUAY)
        )

    def system_prompt(self):
        return (
            "Sos un analista de oportunidades de negocio enfocado en Paraguay y LATAM. "
            "Te paso una lista de posts y productos publicados en las últimas 24h "
            "extraídos de Product Hunt, Hacker News, Reddit, IndieHackers y similares.\n\n"
            "Tu trabajo es responder 3 preguntas:\n"
            "1. ¿Qué problema aparece repetidamente en estas fuentes?\n"
            "2. ¿Qué MVP podría venderse en Paraguay y/o LATAM, considerando el mercado local?\n"
            "3. ¿Hay poca competencia en ese nicho, o está saturado?\n\n"
            "Reglas:\n"
            "- Escribí SIEMPRE en español (incluso si los items están en inglés).\n"
            "- Usá voseo argentino (tenés, podés, dejá, querés, hacé, decí).\n"
            "- Tono directo, sin vueltas, tipo newsletter de negocios.\n"
            "- Máximo 4 oportunidades por resumen, ordenadas por potencial.\n"
            "- Para cada oportunidad:\n"
            "  🎯 Problema: [1 oración]\n"
            "  ✅ MVP sugerido: [1-2 oraciones, concreto y accionable]\n"
            "  💰 Mercado PY/LATAM: [sí/no + razón breve]\n"
            "  ⚔️ Competencia: [baja/media/alta + mención de competidores si conocés]\n"
            "  🔗 Origen: [fuente + título del item que la originó]\n\n"
            "Si no hay oportunidades claras, decilo. No inventes nada que no esté en los items."
        )

    def opciones_llm(self):
        return {"num_predict": 1200, "num_ctx": 4096}

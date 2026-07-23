"""
saas.py
Detector de tendencias SaaS.

Monitorea lanzamientos, crecimiento, funding y movimientos
en el ecosistema SaaS global + LATAM.
"""
from base_agente import AgenteBase

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


class SaaSDetector(AgenteBase):
    nombre = "saas"
    intervalo_horas = 24
    scheduled_times = ["09:30"]
    max_items_por_feed = 15
    max_items_totales = 35
    ntfy_topic = "agente-local-py-saas"
    ntfy_tags = "chart_with_upwards_trend,rocket"
    ntfy_titulo_template = "📊 SaaS Radar — {fecha}"

    feeds = [
        ("SaaStr", "https://www.saastr.com/feed/"),
        ("TechCrunch", "https://techcrunch.com/feed/"),
        ("Product Hunt - SaaS", "https://www.producthunt.com/feed?category=saas"),
        ("Product Hunt - Productivity", "https://www.producthunt.com/feed?category=productivity"),
        ("Reddit SaaS", "https://www.reddit.com/r/SaaS/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("Reddit MicroSaaS", "https://www.reddit.com/r/MicroSaaS/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("ChartMogul", "https://blog.chartmogul.com/feed/"),
        ("Baremetrics", "https://baremetrics.com/blog/rss"),
    ]

    PALABRAS_CLAVE = [
        "saas", "subscription", "mrk", "arr", "churn", "lifetime value",
        "customer acquisition", "pricing", "freemium", "trial",
        "b2b", "b2c", "enterprise", "startup", "funding", "seed",
        "series a", "series b", "growth", "scale", "product-led",
        "plg", "sales-led", "retention", "onboarding", "activation",
        "nps", "unit economics", "cac", "ltv", "gross margin",
        "recurring revenue", "annual contract", "monthly recurring",
    ]

    def filtrar(self, item):
        texto = f"{item.titulo} {item.cuerpo}".lower()
        if "product hunt" in item.fuente.lower():
            return False
        return not any(p in texto for p in self.PALABRAS_CLAVE)

    def system_prompt(self):
        return (
            "Sos un analista del ecosistema SaaS global. Te paso una lista de artículos, "
            "lanzamientos y discusiones de las últimas 24h.\n\n"
            "Extraé las tendencias más relevantes:\n"
            "1. ¿Qué startups levantaron funding y en qué ronda?\n"
            "2. ¿Qué métricas o estrategias de crecimiento están funcionando?\n"
            "3. ¿Qué nichos o verticales están ganando tracción?\n"
            "4. ¿Qué lessons aprendidas comparten los founders?\n\n"
            "Reglas:\n"
            "- Escribí SIEMPRE en español.\n"
            "- Usá voseo argentino (tenés, podés, hacé, decí).\n"
            "- Tono analítico, sin vueltas.\n"
            "- Máximo 5 insights. Para cada uno: tendencia, por qué importa, fuente.\n"
            "- Si no hay nada relevante, decilo. No inventes."
        )

    def opciones_llm(self):
        return {"num_predict": 1000, "num_ctx": 4096}

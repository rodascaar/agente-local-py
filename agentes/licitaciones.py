"""
licitaciones.py
Radar de licitaciones públicas y oportunidades de contratación.

Enfocado en Paraguay (DNCP) y LATAM.
Requiere scraping para fuentes sin RSS (DNCP, COMPR.AR, etc.).
"""
from base_agente import AgenteBase


class LicitacionesAgent(AgenteBase):
    nombre = "licitaciones"
    intervalo_horas = 12
    scheduled_times = ["11:00", "14:00"]
    max_items_por_feed = 15
    max_items_totales = 30
    ntfy_topic = "agente-local-py-licitaciones"
    ntfy_tags = "bank,ledger"
    ntfy_titulo_template = "📋 Licitaciones — {fecha}"

    feeds = [
        ("ONU Compras", "https://www.ungm.org/Publications/RssFeed"),
        ("BID", "https://www.iadb.org/en/rss"),
        ("Banco Mundial", "https://www.worldbank.org/en/rss"),
        ("Reddit Government", "https://www.reddit.com/r/GovernmentContracting/.rss", {"User-Agent": "Mozilla/5.0", "Accept": "application/rss+xml"}),
    ]

    PALABRAS_CLAVE = [
        "licitación", "licitacion", "concurso", "contratación", "contratacion",
        "tender", "procurement", "rfp", "rfq", "bid", "solicitud",
        "obra pública", "obra publica", "provisión", "provision",
        "servicio de", "suministro", "adquisición", "adquisicion",
        "concesión", "concesion", "ppp", "asociación público privada",
        "dncp", "compras públicas", "compras publicas",
        "sipac", "sistema de información", "catálogo", "catalogo",
        "paraguay", "py",
    ]

    def filtrar(self, item):
        texto = f"{item.titulo} {item.cuerpo}".lower()
        return not any(p in texto for p in self.PALABRAS_CLAVE)

    def system_prompt(self):
        return (
            "Sos un analista de licitaciones públicas enfocado en Paraguay y LATAM. "
            "Te paso novedades de las últimas 12h.\n\n"
            "Extraé oportunidades relevantes:\n"
            "1. Licitaciones activas en Paraguay (DNCP o similares)\n"
            "2. Contrataciones internacionales con participación LATAM\n"
            "3. Próximos concursos y plazos\n"
            "4. Adjudicaciones recientes (quién ganó y por cuánto)\n\n"
            "Reglas:\n"
            "- Escribí SIEMPRE en español.\n"
            "- Usá voseo argentino.\n"
            "- Tono directo, tipo alerta de oportunidad.\n"
            "- Incluí monto estimado, plazo y entidad convocante.\n"
            "- Máximo 5 oportunidades. Si no hay nada, decilo.\n\n"
            "Nota: las fuentes RSS de licitaciones públicas son limitadas. "
            "Las oportunidades más relevantes pueden requerir scraping directo "
            "del portal DNCP (Paraguay), COMPR.AR (Argentina) o ChileCompra."
        )

    def opciones_llm(self):
        return {"num_predict": 1000, "num_ctx": 4096}

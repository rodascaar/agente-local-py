"""
finanzas.py
Resumen financiero diario.

Monitorea mercados globales, cripto, economía LATAM,
cotizaciones del dólar, bonos, índices.
"""
from base_agente import AgenteBase

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


class FinanzasAgent(AgenteBase):
    nombre = "finanzas"
    intervalo_horas = 24
    scheduled_times = ["10:30"]
    max_items_por_feed = 10
    max_items_totales = 25
    ntfy_topic = "agente-local-py-finanzas"
    ntfy_tags = "chart,money_with_wings"
    ntfy_titulo_template = "📈 Resumen Financiero — {fecha}"

    feeds = [
        ("Yahoo Finance", "https://finance.yahoo.com/news/rssindex"),
        ("Investing.com", "https://www.investing.com/rss/news.rss"),
        ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        ("Reddit Stocks", "https://www.reddit.com/r/stocks/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("Reddit Crypto", "https://www.reddit.com/r/CryptoCurrency/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("Reddit Economics", "https://www.reddit.com/r/Economics/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
    ]

    PALABRAS_CLAVE = [
        "stock", "market", "nasdaq", "sp500", "dow", "s&p",
        "dólar", "dolar", "blue", "oficial", "ccl", "mep",
        "bitcoin", "btc", "ethereum", "eth", "crypto", "blockchain",
        "inflación", "inflacion", "ipc", "recesión", "recesion",
        "fed", "federal reserve", "bcra", "bcp", "banco central",
        "tasa", "rate", "interest", "fondo", "bond", "bono",
        "emerging market", "emergentes", "latam",
        "paraguay", "py", "pib", "gdp", "deuda", "debt",
        "rendimiento", "yield", "dividend", "earning",
        "quarterly", "earnings", "guidance", "forecast",
    ]

    PALABRAS_NEGATIVO = [
        "nft drop", "airdrop", "memecoin", "shitcoin",
    ]

    def filtrar(self, item):
        texto = f"{item.titulo} {item.cuerpo}".lower()
        if any(p in texto for p in self.PALABRAS_NEGATIVO):
            return True
        return not any(p in texto for p in self.PALABRAS_CLAVE)

    def system_prompt(self):
        return (
            "Sos un analista financiero enfocado en mercados LATAM. "
            "Te paso novedades de las últimas 24h.\n\n"
            "Resumí lo más relevante:\n"
            "1. Cotización del dólar (blue, oficial, CCL, MEP)\n"
            "2. Índices globales (S&P 500, Nasdaq, Dow)\n"
            "3. Cripto: BTC, ETH y movimientos relevantes\n"
            "4. Economía LATAM y Paraguay\n"
            "5. Tasas, bonos y decisiones de bancos centrales\n\n"
            "Reglas:\n"
            "- Escribí SIEMPRE en español.\n"
            "- Usá voseo argentino.\n"
            "- Tono directo, datos precisos, sin opinión.\n"
            "- Incluí números concretos (subió/bajó X%).\n"
            "- Máximo 5 puntos. Si no hay nada relevante, decilo."
        )

    def opciones_llm(self):
        return {"num_predict": 1000, "num_ctx": 4096}

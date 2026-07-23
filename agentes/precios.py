"""
precios.py
Vigilante de precios y ofertas.

Monitorea cambios de precio, ofertas, descuentos
y movimientos en e-commerce y servicios.
NOTA: el monitoreo real de precios requiere scraping.
Este agente rastrea fuentes RSS de ofertas y deals.
"""
from base_agente import AgenteBase


class PreciosAgent(AgenteBase):
    nombre = "precios"
    intervalo_horas = 12
    scheduled_times = ["11:30", "14:30"]
    max_items_por_feed = 10
    max_items_totales = 20
    ntfy_topic = "agente-local-py-precios"
    ntfy_tags = "shopping_cart,dollar"
    ntfy_titulo_template = "💲 Vigilante de Precios — {fecha}"

    feeds = [
        ("Slickdeals", "https://slickdeals.net/newsearch.php?mode=frontpage&searcharea=deals&searchin=first&rss=1"),
        ("DealNews", "https://dealnews.com/rss/"),
    ]

    PALABRAS_CLAVE = [
        "descuento", "discount", "oferta", "offer", "sale", "rebaja",
        "cyber monday", "black friday", "hot sale", "prime day",
        "código", "codigo", "cupón", "cupon", "promo", "promotion",
        "gratis", "free", "envío gratis", "envio gratis",
        "precio", "price", "bajo", "low", "barato", "cheap",
        "50%", "60%", "70%", "80%", "off", "% off",
        "dólar", "dolar", "blue", "oficial", "ccl", "mep",
    ]

    PALABRAS_NEGATIVO = [
        "crypto", "nft", "bitcoin", "airdrop",
    ]

    def filtrar(self, item):
        texto = f"{item.titulo} {item.cuerpo}".lower()
        if any(p in texto for p in self.PALABRAS_NEGATIVO):
            return True
        return not any(p in texto for p in self.PALABRAS_CLAVE)

    def system_prompt(self):
        return (
            "Sos un vigilante de precios y ofertas para LATAM. "
            "Te paso novedades de las últimas 12h.\n\n"
            "Resumí las mejores ofertas:\n"
            "1. Descuentos reales (no inflados)\n"
            "2. Productos con buena relación precio/calidad\n"
            "3. Ofertas que apliquen a envío a Paraguay/LATAM\n"
            "4. Movimientos del dólar si afectan precios\n\n"
            "Reglas:\n"
            "- Escribí SIEMPRE en español.\n"
            "- Usá voseo argentino.\n"
            "- Tono directo, tipo alerta.\n"
            "- Incluí precio original vs oferta, y link directo.\n"
            "- Si no hay nada relevante, decilo.\n\n"
            "Nota: para monitoreo real de precios en e-commerce "
            "paraguayo (Shopping, Superseis, etc.) se necesita un scraper dedicado."
        )

    def opciones_llm(self):
        return {"num_predict": 800, "num_ctx": 3072}

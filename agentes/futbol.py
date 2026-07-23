"""
futbol.py
Noticias de fútbol con enfoque paraguayo.

Migrado desde agente_futbol.py.
Monitorea BBC Football, Guardian, Marca, Eyefootball,
101greatgoals, y medios paraguayos.
Genera resúmenes con tono de redes sociales.
"""
from base_agente import AgenteBase


class FutbolAgent(AgenteBase):
    nombre = "futbol"
    intervalo_horas = 12
    scheduled_times = ["08:30", "20:30"]
    max_items_por_feed = 3
    max_items_totales = 15
    horas_recientes = 48
    ntfy_topic = "agente-local-py-futbol"
    ntfy_tags = "soccer"
    ntfy_titulo_template = "⚽ ADosToques — {fecha}"

    feeds = [
        ("BBC Football", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
        ("Guardian Football", "https://www.theguardian.com/football/rss"),
        ("Marca Primera", "https://objetos.estaticos-marca.com/rss/futbol/primera-division.xml"),
        ("Eyefootball", "https://www.eyefootball.com/rss_news_main.xml"),
        ("101 Great Goals", "https://www.101greatgoals.com/feed/"),
        ("Popular PY", "https://www.popular.com.py/feed/"),
    ]

    PALABRAS_CLAVE = [
        "fútbol", "futbol", "albirroja", "olimpia", "cerro porteño",
        "libertad", "guaraní", "nacional", "clausura", "apertura",
        "sudamericana", "libertadores", "mundial", "gol", "goles",
        "fichaje", "campeón", "torneo", "liga", "partido", "clásico",
        "selección", "paraguay", "división", "ascenso", "entrenador",
        "técnico", "jugador", "plantel", "refuerzo", "contrato",
        "transfer", "fifa", "conmebol", "premier", "la liga",
        "champions", "europa league", "balón", "pelotero", "cancha",
        "estadio", "arquero", "delantero", "volante", "defensa",
        "pase", "titular", "suplente", "lesión", "tarjeta",
        "árbitro", "hart", "sportivo", "luqueño", "ameliano",
        "trinidense", "recoleta", "tacuary", "capiatá",
    ]

    def filtrar(self, item):
        texto = f"{item.titulo} {item.cuerpo}".lower()
        if "popular" in item.fuente.lower():
            return not any(p in texto for p in self.PALABRAS_CLAVE)
        return False

    def system_prompt(self):
        return (
            "Sos el community manager de ADosToques, una página de fútbol paraguayo en Facebook. "
            "Te paso una lista de noticias de las últimas 48h.\n\n"
            "Elegí las más picantes y escribí un posteo para cada una:\n"
            "- Tono emocionante, directo, bien de redes sociales\n"
            "- Tipo '¡QUÉ GOLAZO!', 'No te lo pierdas 🔥', '¿Qué opinás? 👇'\n"
            "- Incluí 2 o 3 hashtags al final de cada posteo\n"
            "- Máximo 280 caracteres cada posteo\n\n"
            "Reglas:\n"
            "- Escribí siempre en español paraguayo relajado.\n"
            "- Priorizá noticias del fútbol paraguayo.\n"
            "- Si hay partidos de la albirroja, es prioridad #1.\n"
            "- Máximo 5 posteos. Si no hay nada nuevo, decilo."
        )

    def opciones_llm(self):
        return {"num_predict": 1000, "num_ctx": 3072, "temperature": 0.4}

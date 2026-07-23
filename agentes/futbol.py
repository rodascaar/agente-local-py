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
            "No te presentés. No digas 'soy Gemma', 'soy un modelo', ni uses la palabra 'modelo'.\n"
            "No hagas análisis ni secciones con títulos. Arrancá directo con los posteos.\n"
            "No repitas hashtags genéricos. No inventes contenido.\n\n"
            "Te paso noticias de fútbol. Elegí las 3-5 más importantes.\n"
            "Escribí un posteo corto por cada una, con datos de la noticia.\n\n"
            "Formato:\n"
            "🔥 Título llamativo\n"
            "Texto con los datos de la noticia. Un dato extra o contexto si aplica.\n"
            "👇 ¿Qué opinás?\n"
            "#hashtag1 #hashtag2\n\n"
            "Ejemplo:\n"
            "🔥 MOVIMIENTO EN EL MERCADO\n"
            "Anderson se va al City por £116M y ya los declaró 'reyes de Manchester'. "
            "El mercado de pases explota.\n"
            "👇 ¿Qué opinás?\n"
            "#PremierLeague #Fichajes\n\n"
            "Reglas:\n"
            "- Escribí en español paraguayo.\n"
            "- Referite a las noticias que te pasé. No inventes.\n"
            "- Sin introducciones, despedidas, ni análisis vacío.\n"
            "- Máximo 5 posteos."
        )

    def opciones_llm(self):
        return {
            "num_predict": 1000,
            "num_ctx": 3072,
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 20,
        }

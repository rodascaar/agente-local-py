"""
noticias.py
Curador de noticias de IA y tecnología.

Migrado desde agente_ia.py.
Monitorea OpenAI, HuggingFace, MIT Tech Review, VentureBeat,
The Verge, Wired, Ars Technica, y referentes (Vercel, DeepMind, NVIDIA, arXiv).
"""
from base_agente import AgenteBase


class NoticiasAgent(AgenteBase):
    nombre = "noticias"
    intervalo_horas = 12
    scheduled_times = ["08:00", "20:00"]
    max_items_por_feed = 3
    max_items_totales = 20
    horas_recientes = 48
    ntfy_topic = "agente-local-py-noticias"
    ntfy_tags = "robot"
    ntfy_titulo_template = "🤖 IA Radar — {fecha}"

    feeds = [
        ("OpenAI", "https://openai.com/news/rss.xml"),
        ("HuggingFace", "https://huggingface.co/blog/feed.xml"),
        ("MIT Tech Review", "https://www.technologyreview.com/topic/artificial-intelligence/feed/"),
        ("VentureBeat", "https://venturebeat.com/category/ai/feed/"),
        ("MarkTechPost", "https://www.marktechpost.com/feed/"),
        ("The Verge AI", "https://www.theverge.com/ai-artificial-intelligence/rss.xml"),
        ("Wired AI", "https://www.wired.com/feed/tag/ai/latest/rss"),
        ("Ars Technica AI", "https://feeds.arstechnica.com/arstechnica/ai"),
        ("Vercel", "https://vercel.com/atom"),
        ("DeepMind", "https://deepmind.google/blog/rss.xml"),
        ("NVIDIA", "https://developer.nvidia.com/blog/feed/"),
        ("arXiv cs.AI", "https://export.arxiv.org/rss/cs.ai"),
    ]

    PALABRAS_CLAVE = [
        "gpt", "openai", "anthropic", "claude", "gemma", "gemini", "llama",
        "mistral", "deepseek", "qwen", "mixtral", "phi", "olmo", "dbrx",
        "cohere", "command r", "nemotron", "kimi", "moonshot", "yi",
        "modelo", "model", "llm", "lenguaje", "inteligencia artificial",
        "artificial intelligence", "machine learning", "deep learning",
        "transformers", "neural network", "inferencia", "inference",
        "entrenamiento", "training", "fine-tuning", "rlhf", "rag",
        "agente", "agent", "nvidia", "h100", "h200", "b200", "b100",
        "data center", "datacenter", "open source", "código abierto",
        "paper", "arxiv", "investigación", "research", "chatgpt",
        "copilot", "grok", "xai", "meta ai", "google deepmind",
        "ia local", "local ai", "edge ai", "on-device", "stargate",
    ]

    def filtrar(self, item):
        texto = f"{item.titulo} {item.cuerpo}".lower()
        if "vercel" in item.fuente.lower() or "deepmind" in item.fuente.lower() or "nvidia" in item.fuente.lower():
            return False
        return not any(p in texto for p in self.PALABRAS_CLAVE)

    def system_prompt(self):
        return (
            "Sos un curador de noticias de IA y tecnología. "
            "Te paso una lista de noticias de las últimas 48h.\n\n"
            "Resumí las más importantes. Para cada noticia:\n"
            "- 1 oración con tono directo, tipo LinkedIn\n"
            "- Decí qué pasó, quién lo hizo y por qué importa\n"
            "- Incluí 1 o 2 hashtags relevantes\n\n"
            "Reglas:\n"
            "- Escribí SIEMPRE en español (incluso si la fuente está en inglés).\n"
            "- Usá voseo argentino (tenés, podés, hacé, decí).\n"
            "- Tono directo, sin marketinero.\n"
            "- Priorizá lo que tenga más impacto.\n"
            "- Máximo 8 noticias. Si no hay nada nuevo, decilo."
        )

    def opciones_llm(self):
        return {"num_predict": 1200, "num_ctx": 4096, "temperature": 0.3}

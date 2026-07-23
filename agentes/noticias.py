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
        ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
        ("Wired AI", "https://www.wired.com/feed/tag/ai/latest/rss"),
        ("Ars Technica AI", "https://arstechnica.com/ai/feed/"),
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
            "Sos un curador de noticias de IA con tono LinkedIn argentino.\n\n"
            "Te paso noticias recientes. Resumí las más importantes (máx 8).\n\n"
            "Cada noticia en UNA línea con este formato exacto:\n"
            "- [Fuente] Qué pasó, quién lo hizo, por qué importa. #hashtag\n\n"
            "Ejemplo:\n"
            "- [OpenAI] OpenAI lanzó GPT-5 con razonamiento nivel doctorado, "
            "marcando un salto enorme en capacidades de IA #OpenAI #GPT5\n"
            "- [HuggingFace] HuggingFace presentó un modelo de código abierto "
            "que supera a GPT-4 en benchmarks, democratizando el acceso a IA "
            "avanzada #OpenSource\n\n"
            "Reglas:\n"
            "- Escribí SIEMPRE en español argentino con voseo "
            "(tenés, podés, decí, hacé, están discutiendo).\n"
            "- COMPLETÁ las frases hasta el final. NUNCA dejes oraciones truncadas.\n"
            "- Priorizá impacto. Si no hay nada nuevo, decilo."
        )

    def opciones_llm(self):
        return {
            "num_predict": 1200,
            "num_ctx": 4096,
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 20,
        }

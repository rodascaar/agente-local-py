"""
github_radar.py
Radar de repositorios y proyectos open source.

Monitorea GitHub Trending, repos nuevos relevantes,
lanzamientos de herramientas y frameworks.
"""
from base_agente import AgenteBase

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


class GitHubRadar(AgenteBase):
    nombre = "github_radar"
    intervalo_horas = 24
    scheduled_times = ["10:00"]
    max_items_por_feed = 10
    max_items_totales = 25
    ntfy_topic = "agente-local-py-github"
    ntfy_tags = "hammer_and_wrench,star"
    ntfy_titulo_template = "⭐ GitHub Radar — {fecha}"

    feeds = [
        ("GitHub Blog", "https://github.blog/feed/"),
        ("HN Show", "https://news.ycombinator.com/showrss"),
        ("Reddit Programming", "https://www.reddit.com/r/programming/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("Reddit OpenSource", "https://www.reddit.com/r/opensource/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("Reddit Golang", "https://www.reddit.com/r/golang/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("Reddit Python", "https://www.reddit.com/r/Python/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("Reddit Rust", "https://www.reddit.com/r/rust/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("Reddit JavaScript", "https://www.reddit.com/r/javascript/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
    ]

    PALABRAS_CLAVE = [
        "release", "launch", "new tool", "framework", "library",
        "open source", "código abierto", "repository", "repo",
        "cli", "api", "sdk", "npm", "pip", "cargo", "go mod",
        "github", "gitlab", "self-hosted", "selfhosted",
        "alternative to", "drop-in replacement", "rewrite in",
        "v0.", "v1.", "v2.", "version", "beta", "alpha",
        "show hn", "showdev",
    ]

    PALABRAS_NEGATIVO = [
        "hiring", "job", "career", "salary",
    ]

    def filtrar(self, item):
        texto = f"{item.titulo} {item.cuerpo}".lower()
        if any(p in texto for p in self.PALABRAS_NEGATIVO):
            return True
        if "hn show" in item.fuente.lower():
            return False
        return not any(p in texto for p in self.PALABRAS_CLAVE)

    def system_prompt(self):
        return (
            "Sos un curador de herramientas open source y proyectos nuevos. "
            "Te paso lanzamientos de las últimas 24h.\n\n"
            "Seleccioná los proyectos más relevantes:\n"
            "1. Herramientas que resuelven un problema real\n"
            "2. Frameworks o librerías que ganan tracción\n"
            "3. Alternativas open source a herramientas pagas\n"
            "4. Proyectos interesantes en Go, Rust, Python, JS\n\n"
            "Reglas:\n"
            "- Escribí SIEMPRE en español.\n"
            "- Usá voseo argentino.\n"
            "- Tono seco, tipo recomendación técnica.\n"
            "- Para cada proyecto: qué hace, lenguaje, stars actuales.\n"
            "- Máximo 5 proyectos. Solo lo que te parezca útil."
        )

    def opciones_llm(self):
        return {"num_predict": 1000, "num_ctx": 4096}

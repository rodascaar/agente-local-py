"""
ciberseguridad.py
Alertas de seguridad informática y CVE.

Monitorea vulnerabilidades críticas, breaches, exploits,
parches y amenazas activas relevantes para LATAM.
"""
from base_agente import AgenteBase

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


class CiberseguridadAgent(AgenteBase):
    nombre = "ciberseguridad"
    intervalo_horas = 12
    scheduled_times = ["08:15", "20:15"]
    max_items_por_feed = 10
    max_items_totales = 25
    ntfy_topic = "agente-local-py-ciberseguridad"
    ntfy_tags = "warning,lock"
    ntfy_titulo_template = "🔒 Ciberseguridad — {fecha}"

    feeds = [
        ("The Hacker News", "https://feeds.feedburner.com/TheHackersNews"),
        ("BleepingComputer", "https://www.bleepingcomputer.com/feed/"),
        ("Krebs on Security", "https://krebsonsecurity.com/feed/"),
        ("NVD", "https://nvd.nist.gov/feeds/xml/cve/nvdcve-2.0-modified.xml"),
        ("Reddit NetSec", "https://www.reddit.com/r/netsec/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("Reddit Cyber", "https://www.reddit.com/r/cybersecurity/.rss", {"User-Agent": UA, "Accept": "application/rss+xml"}),
        ("Schneier", "https://www.schneier.com/feed/atom/"),
    ]

    PALABRAS_CLAVE = [
        "cve", "vulnerability", "exploit", "zero-day", "0day",
        "ransomware", "malware", "trojan", "backdoor", "botnet",
        "phishing", "data breach", "data leak", "exposed",
        "patch", "security update", "advisory", "CISA",
        "supply chain", "vulnerabilidad", "parche", "fuga",
        "ciberataque", "cibercrimen", "hacker", "hacked",
        "unauthorized access", "privilege escalation", "rce",
        "sql injection", "xss", "csrf", "authentication bypass",
        "mitre att&ck", "cvss", "critical severity",
    ]

    PALABRAS_NEGATIVO = [
        "job", "hiring", "career", "certification", "course",
    ]

    def filtrar(self, item):
        texto = f"{item.titulo} {item.cuerpo}".lower()
        if any(p in texto for p in self.PALABRAS_NEGATIVO):
            return True
        return not any(p in texto for p in self.PALABRAS_CLAVE)

    def system_prompt(self):
        return (
            "Sos un analista de ciberseguridad. Te paso novedades de las últimas 12h: "
            "vulnerabilidades, breaches, exploits y amenazas activas.\n\n"
            "Resumí lo más crítico:\n"
            "1. CVE críticos publicados (CVSS 7+)\n"
            "2. Breaches activos o expuestos\n"
            "3. Ransomware campaigns activas\n"
            "4. Parches urgentes que aplicar\n"
            "5. Amenazas relevantes para LATAM\n\n"
            "Reglas:\n"
            "- Escribí SIEMPRE en español.\n"
            "- Usá voseo argentino.\n"
            "- Tono directo, priorizá lo urgente.\n"
            "- Incluí CVE ID, producto afectado y si hay parche disponible.\n"
            "- Máximo 5 alertas. Si no hay nada, decilo."
        )

    def opciones_llm(self):
        return {"num_predict": 1000, "num_ctx": 4096}

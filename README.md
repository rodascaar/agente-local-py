# agente-local-py

Motor modular de agentes AI que monitorean feeds RSS, resumen con LLM local y notifican por [ntfy.sh](https://ntfy.sh).

## Requisitos

- Python 3.10+
- `pip install -r requirements.txt`
- Un backend LLM corriendo (al menos uno):
  - **llama.cpp** (`llama-server` con `gemma-4-E2B` en `http://127.0.0.1:8080`)
  - **Ollama** (ej. `qwen2.5:1.5b` en `http://127.0.0.1:11434`)

Auto-detecta cuál está disponible. Prefiere llama.cpp, fallback a Ollama.

## Uso

```bash
# Listar agentes disponibles
python main.py --list

# Ejecutar un agente una vez
python main.py --run noticias

# Modo daemon (ejecuta según horarios configurados)
python main.py --daemon
```

## Agentes

| Agente | Horario | Descripción |
|--------|---------|-------------|
| `noticias` | 08:00 / 20:00 | IA y tecnología (OpenAI, HuggingFace, MIT, NVIDIA, arXiv, Vercel...) |
| `ciberseguridad` | 08:15 / 20:15 | CVE, breaches, exploits (HN, BleepingComputer, Krebs, NVD...) |
| `futbol` | 08:30 / 20:30 | Fútbol paraguayo (BBC, Guardian, Marca, Popular PY...) |
| `startups` | 09:00 | Oportunidades de negocio (Product Hunt, HN, Reddit, SaaStr...) |
| `saas` | 09:30 | Tendencias SaaS (SaaStr, TechCrunch, PH, ChartMogul...) |
| `github_radar` | 10:00 | Open source y repos nuevos (GH Blog, Show HN, Reddit langs...) |
| `finanzas` | 10:30 | Mercados, dólar, cripto (Yahoo, Investing, CoinDesk...) |
| `licitaciones` | 11:00 / 14:00 | Contratación pública PY/LATAM (ONU, BID, BM...) |
| `precios` | 11:30 / 14:30 | Ofertas y descuentos (Slickdeals, DealNews...) |

## Configuración

Crear `config.json` en la raíz del proyecto para sobrescribir defaults:

```json
{
  "llm": {
    "backend": "llama",
    "timeout": 300
  },
  "ntfy": {
    "default_topic": "mi-topic-personal"
  },
  "scheduler": {
    "spacing_entre_agentes": 600
  }
}
```

Parámetros disponibles:

| Clave | Default | Descripción |
|-------|---------|-------------|
| `llm.backend` | `auto` | `auto`, `llama`, `ollama` |
| `llm.llama_url` | `http://127.0.0.1:8080` | URL de llama-server |
| `llm.ollama_url` | `http://127.0.0.1:11434` | URL de Ollama |
| `llm.timeout` | `180` | Timeout de llamadas al LLM |
| `ntfy.default_topic` | `agente-local-py-default` | Topic por defecto |
| `scheduler.spacing_entre_agentes` | `300` | Pausa (seg) entre agentes |
| `scheduler.ventana_horaria_minutos` | `120` | Tolerancia para horarios perdidos |

## Arquitectura

```
agente-base/
├── config.py          # Config central con auto-detect + override
├── llm.py             # Unifica llama.cpp + Ollama con fallback
├── feeds.py           # Parser RSS/Atom con fallback regex
├── cache.py           # Cache persistente por agente (dict-based, thread-safe)
├── ntfy.py            # Notificaciones push con reintentos
├── base_agente.py     # Clase base abstracta con chunking automático
├── scheduler.py       # Daemon loop con horarios escalonados
├── main.py            # CLI entry point (--run / --daemon / --list)
├── agentes/           # Agentes concretos (uno por archivo)
└── cache/             # JSONs de items vistos (gitignored)
```

Cada agente hereda de `AgenteBase`. Para crear uno nuevo:

```python
from base_agente import AgenteBase

class MiAgente(AgenteBase):
    nombre = "miagente"
    intervalo_horas = 12
    scheduled_times = ["09:00", "18:00"]
    ntfy_topic = "agente-local-py-miagente"
    feeds = [
        ("Mi Feed", "https://ejemplo.com/rss"),
    ]

    def system_prompt(self):
        return "Sos un analista de..."

    def filtrar(self, item):
        return False  # True descarta el item
```

Se auto-descubre al ejecutar `--list`, `--run miagente`, o `--daemon`.

## Chunking automático

Si los items de los feeds no entran en el contexto del LLM (`num_ctx`), el sistema:
1. Parte los items en chunks que entran en el contexto
2. Resume cada chunk por separado
3. Mergea los resúmenes parciales en un informe final

Esto permite procesar decenas de items incluso con modelos de contexto limitado (2048-4096 tokens).

## Notas

- El scheduler respeta horarios escalonados para no saturar el LLM
- Entre agente y agente hay un spacing configurable (default 5 min)
- Los topics de ntfy están namespaced con `agente-local-py-` para evitar colisiones
- `config.json`, `cache/` y `__pycache__/` están en `.gitignore`

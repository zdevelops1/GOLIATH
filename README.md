# GOLIATH

**Universal AI Automation Engine**

GOLIATH is a modular, plugin-driven automation engine that takes plain-English tasks and executes them through AI. Built on the xAI Grok API by default, it's designed so any model provider or third-party integration can be dropped in as a plugin with zero changes to the core.

## Architecture

```
goliath/
  main.py              # Entry point (interactive & single-shot modes)
  config.py            # API keys, model settings, plugin registry
  core/
    engine.py          # Task execution engine — orchestrates everything
  models/
    base.py            # Abstract provider interface
    grok.py            # xAI Grok provider (default)
    openai_provider.py # OpenAI provider (GPT-4o, GPT-4, etc.)
    claude.py          # Anthropic Claude provider (Opus, Sonnet, Haiku)
    gemini.py          # Google Gemini provider (2.0 Flash, 1.5 Pro)
  integrations/        # Third-party service plugins (Slack, GitHub, etc.)
  tools/               # Executable tool plugins (web search, file I/O, etc.)
  memory/              # Persistent context & session memory
  cli/
    interface.py       # Interactive REPL & single-shot CLI
```

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/goliath.git
cd goliath

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your API key(s) — at minimum the default provider (Grok)
export XAI_API_KEY="your-key-here"
# Optional: enable additional providers
# export OPENAI_API_KEY="your-key-here"
# export ANTHROPIC_API_KEY="your-key-here"
# export GOOGLE_API_KEY="your-key-here"

# 4. Run GOLIATH
python main.py
```

You'll get an interactive prompt where you can type any task:

```
GOLIATH > Summarise the top 5 trends in AI this week
```

Or run a single task directly:

```bash
python main.py "Write a Python script that sorts a list of names"
```

## Supported Providers

| Provider | Config Key | Default Model |
|---|---|---|
| **xAI Grok** (default) | `XAI_API_KEY` | `grok-3-latest` |
| **OpenAI** | `OPENAI_API_KEY` | `gpt-4o` |
| **Anthropic Claude** | `ANTHROPIC_API_KEY` | `claude-sonnet-4-5-20250929` |
| **Google Gemini** | `GOOGLE_API_KEY` | `gemini-2.0-flash` |

Switch providers by setting `DEFAULT_PROVIDER` in `config.py` (or `.env`):

```python
DEFAULT_PROVIDER = "claude"  # or "openai", "gemini", "grok"
```

## Adding a New Model Provider

1. Create a new file in `models/` (e.g. `models/my_provider.py`).
2. Subclass `BaseProvider` from `models/base.py` and implement `run()`.
3. Register it in `config.py`:

```python
MODEL_PROVIDERS = {
    ...
    "my_provider": "models.my_provider",
}
```

4. Set `DEFAULT_PROVIDER = "my_provider"` — no other code needs to change.

## Adding an Integration

Drop a module into `integrations/`, register it in `config.INTEGRATIONS`, and the engine can discover and use it. The same pattern applies to `tools/` for executable tool plugins.

## Configuration

All settings live in `config.py` and can be overridden with environment variables:

| Variable | Default | Description |
|---|---|---|
| `XAI_API_KEY` | — | xAI API key |
| `XAI_DEFAULT_MODEL` | `grok-3-latest` | Grok model |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OPENAI_DEFAULT_MODEL` | `gpt-4o` | OpenAI model |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `ANTHROPIC_DEFAULT_MODEL` | `claude-sonnet-4-5-20250929` | Claude model |
| `GOOGLE_API_KEY` | — | Google AI API key |
| `GOOGLE_DEFAULT_MODEL` | `gemini-2.0-flash` | Gemini model |
| `DEFAULT_PROVIDER` | `grok` | Which provider to use |

## License

MIT

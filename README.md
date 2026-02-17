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

# 3. Set your xAI API key
export XAI_API_KEY="your-key-here"

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

## Adding a New Model Provider

1. Create a new file in `models/` (e.g. `models/openai_provider.py`).
2. Subclass `BaseProvider` from `models/base.py` and implement `run()`.
3. Register it in `config.py`:

```python
MODEL_PROVIDERS = {
    "grok": "models.grok",
    "openai": "models.openai_provider",  # new
}
```

4. Switch to it by setting `DEFAULT_PROVIDER = "openai"` in `config.py`, or pass it to the engine directly.

That's it. No other code needs to change.

## Adding an Integration

Drop a module into `integrations/`, register it in `config.INTEGRATIONS`, and the engine can discover and use it. The same pattern applies to `tools/` for executable tool plugins.

## Configuration

All settings live in `config.py` and can be overridden with environment variables:

| Variable | Default | Description |
|---|---|---|
| `XAI_API_KEY` | — | Your xAI API key (required) |
| `XAI_BASE_URL` | `https://api.x.ai/v1` | xAI API endpoint |
| `XAI_DEFAULT_MODEL` | `grok-3-latest` | Which Grok model to use |

## License

MIT

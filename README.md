# GOLIATH

**Universal AI Automation Engine**

GOLIATH is a modular, plugin-driven automation engine that takes plain-English tasks and executes them through AI. Built on the xAI Grok API by default, with drop-in support for OpenAI, Anthropic Claude, and Google Gemini. Any model provider or third-party integration can be added as a plugin with zero changes to the core.

## Supported Providers

| Provider | Status | Default Model | Plugin File |
|---|---|---|---|
| **xAI Grok** | Default | `grok-3-latest` | `models/grok.py` |
| **OpenAI** | Ready | `gpt-4o` | `models/openai_provider.py` |
| **Anthropic Claude** | Ready | `claude-sonnet-4-5-20250929` | `models/claude.py` |
| **Google Gemini** | Ready | `gemini-2.0-flash` | `models/gemini.py` |

All four providers are built in. Add the API key and go — no code changes needed.

## Quick Start

```bash
# Clone the repo
git clone https://github.com/zdevelops1/GOLIATH.git
cd GOLIATH

# Install dependencies
pip install -r requirements.txt
```

### Set Up API Keys

Create a `.env` file in the project root (this file is git-ignored and will never be committed):

```bash
# Required — default provider
XAI_API_KEY=your-xai-key-here

# Optional — enable additional providers
OPENAI_API_KEY=your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
GOOGLE_API_KEY=your-google-key-here
```

Or export them directly:

```bash
export XAI_API_KEY="your-xai-key-here"
```

### Run GOLIATH

**Interactive mode** — opens a REPL where you type tasks:

```bash
python main.py
```

```
   ██████   ██████  ██      ██  █████  ████████ ██   ██
  ██       ██    ██ ██      ██ ██   ██    ██    ██   ██
  ██   ███ ██    ██ ██      ██ ███████    ██    ███████
  ██    ██ ██    ██ ██      ██ ██   ██    ██    ██   ██
   ██████   ██████  ███████ ██ ██   ██    ██    ██   ██

  Universal AI Automation Engine
  Type a task. Type 'quit' to exit.

GOLIATH > Summarise the top 5 trends in AI this week
```

**Single-shot mode** — pass a task directly:

```bash
python main.py "Write a Python script that sorts a list of names"
```

### Switch Providers

Change the default provider in your `.env` or `config.py`:

```
DEFAULT_PROVIDER=claude
```

Options: `grok` (default), `openai`, `claude`, `gemini`

## Architecture

```
goliath/
  main.py              # Entry point (interactive & single-shot modes)
  config.py            # API keys, model settings, plugin registry
  core/
    engine.py          # Task execution engine — orchestrates everything
  models/
    base.py            # Abstract provider interface (subclass to add new models)
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

## Adding a New Model Provider

1. Create a file in `models/` (e.g. `models/my_provider.py`)
2. Subclass `BaseProvider` from `models/base.py` and implement `run()`
3. Register it in `config.py`:

```python
MODEL_PROVIDERS = {
    ...
    "my_provider": "models.my_provider",
}
```

4. Set `DEFAULT_PROVIDER = "my_provider"` — no other code needs to change

## Adding an Integration

Drop a module into `integrations/`, register it in `config.INTEGRATIONS`, and the engine can discover and use it. The same pattern applies to `tools/` for executable tool plugins.

## Configuration Reference

All settings live in `config.py` and can be overridden with environment variables or `.env`:

| Variable | Default | Description |
|---|---|---|
| `DEFAULT_PROVIDER` | `grok` | Active model provider |
| `XAI_API_KEY` | — | xAI API key |
| `XAI_DEFAULT_MODEL` | `grok-3-latest` | Grok model |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `OPENAI_DEFAULT_MODEL` | `gpt-4o` | OpenAI model |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `ANTHROPIC_DEFAULT_MODEL` | `claude-sonnet-4-5-20250929` | Claude model |
| `GOOGLE_API_KEY` | — | Google AI API key |
| `GOOGLE_DEFAULT_MODEL` | `gemini-2.0-flash` | Gemini model |

## License

MIT

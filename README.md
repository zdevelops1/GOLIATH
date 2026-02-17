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

## Install

**From PyPI:**

```bash
pip install goliath-ai
```

**From source:**

```bash
git clone https://github.com/zdevelops1/GOLIATH.git
cd GOLIATH
pip install -e .
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
goliath          # if installed via pip
python main.py   # if running from source
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
goliath "Write a Python script that sorts a list of names"
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
  main.py                # Entry point & CLI entrypoint
  pyproject.toml         # Package config (pip install goliath-ai)
  src/goliath/
    __init__.py          # Package root
    config.py            # API keys, model settings, plugin registry
    main.py              # CLI dispatcher (interactive & single-shot)
    core/
      engine.py          # Task execution engine — orchestrates everything
    models/
      base.py            # Abstract provider interface (subclass to add new models)
      grok.py            # xAI Grok provider (default)
      openai_provider.py # OpenAI provider (GPT-4o, GPT-4, etc.)
      claude.py          # Anthropic Claude provider (Opus, Sonnet, Haiku)
      gemini.py          # Google Gemini provider (2.0 Flash, 1.5 Pro)
    integrations/
      x.py               # X / Twitter (tweets, threads, media)
      instagram.py       # Instagram (photos, Reels, carousels)
      discord.py         # Discord (messages, embeds, files via webhook)
      telegram.py        # Telegram (messages, photos, documents via bot)
      gmail.py           # Gmail (emails with HTML, attachments via SMTP)
      scraper.py         # Web scraper (text, links, structured data)
      slack.py           # Slack (messages, Block Kit, file uploads)
      github.py          # GitHub (repos, issues, PRs, files, Actions)
    tools/               # Executable tool plugins (web search, file I/O, etc.)
    memory/              # Persistent context & session memory
    cli/
      interface.py       # Interactive REPL & single-shot CLI
```

## Adding a New Model Provider

1. Create a file in `src/goliath/models/` (e.g. `my_provider.py`)
2. Subclass `BaseProvider` from `goliath.models.base` and implement `run()`
3. Register it in `src/goliath/config.py`:

```python
MODEL_PROVIDERS = {
    ...
    "my_provider": "goliath.models.my_provider",
}
```

4. Set `DEFAULT_PROVIDER = "my_provider"` — no other code needs to change

## Integrations

Eight built-in integrations for connecting GOLIATH to external services:

| Integration | What it does | Setup |
|---|---|---|
| **X / Twitter** | Post tweets, threads, and media | 4 OAuth keys from [developer.x.com](https://developer.x.com) |
| **Instagram** | Post photos, Reels, and carousels | Meta Graph API token ([setup guide](src/goliath/integrations/instagram.py)) |
| **Discord** | Send messages, rich embeds, and files | Webhook URL (no auth needed) |
| **Telegram** | Send messages, photos, and documents | Bot token from [@BotFather](https://t.me/BotFather) |
| **Gmail** | Send emails with HTML and attachments | App password from [Google](https://myaccount.google.com/apppasswords) |
| **Slack** | Send messages, Block Kit, and file uploads | Webhook URL or bot token from [api.slack.com](https://api.slack.com/apps) |
| **GitHub** | Manage repos, issues, PRs, files, and Actions | Personal access token from [github.com/settings/tokens](https://github.com/settings/tokens) |
| **Web Scraper** | Extract text, links, and data from URLs | No keys needed |

### Quick Examples

```python
from goliath.integrations.x import XClient
from goliath.integrations.instagram import InstagramClient
from goliath.integrations.discord import DiscordClient
from goliath.integrations.telegram import TelegramClient
from goliath.integrations.gmail import GmailClient
from goliath.integrations.slack import SlackClient
from goliath.integrations.github import GitHubClient
from goliath.integrations.scraper import WebScraper

# Post a tweet
XClient().tweet("Hello from GOLIATH!")

# Post a photo to Instagram
InstagramClient().post_image("https://example.com/photo.jpg", caption="Automated post")

# Send a Discord message with a rich embed
DiscordClient().send_embed(title="Deploy Complete", description="v1.0 is live.", color=0x00FF00)

# Send a Telegram message
TelegramClient().send("Build finished successfully.")

# Send an email with an attachment
GmailClient().send(to="team@example.com", subject="Report", body="See attached.", attachments=["report.pdf"])

# Send a Slack message with Block Kit
SlackClient().send("Deployment complete.", channel="#deployments")

# Create a GitHub issue
GitHubClient().create_issue("owner/repo", title="Bug report", body="Something broke.")

# Scrape a web page
data = WebScraper().get_text("https://example.com")
```

Each integration file contains full setup instructions in its docstring.

## Adding a New Integration

Drop a module into `src/goliath/integrations/`, register it in `config.INTEGRATIONS`, and the engine can discover and use it. The same pattern applies to `tools/` for executable tool plugins.

## Configuration Reference

All settings live in `config.py` and can be overridden with environment variables or `.env`:

**Model Providers**

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

**Integrations**

| Variable | Description |
|---|---|
| `X_CONSUMER_KEY` | X/Twitter API key |
| `X_CONSUMER_SECRET` | X/Twitter API secret |
| `X_ACCESS_TOKEN` | X/Twitter access token |
| `X_ACCESS_TOKEN_SECRET` | X/Twitter access token secret |
| `INSTAGRAM_USER_ID` | Instagram Business account ID |
| `INSTAGRAM_ACCESS_TOKEN` | Meta Graph API access token |
| `DISCORD_WEBHOOK_URL` | Discord channel webhook URL |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Default Telegram chat/group ID |
| `GMAIL_ADDRESS` | Gmail address to send from |
| `GMAIL_APP_PASSWORD` | Gmail app password |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook URL |
| `SLACK_BOT_TOKEN` | Slack bot user OAuth token |
| `GITHUB_TOKEN` | GitHub personal access token |
| `GITHUB_OWNER` | Default GitHub user or org name |

## License

MIT

# GOLIATH

[![CI](https://github.com/zdevelops1/GOLIATH/actions/workflows/ci.yml/badge.svg)](https://github.com/zdevelops1/GOLIATH/actions/workflows/ci.yml)

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
      moderation.py      # Content moderation — screens tasks before the model
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
      imagegen.py        # Image generation (DALL-E text-to-image, edits, variations)
      sheets.py          # Google Sheets (read, write, append, create)
      drive.py           # Google Drive (upload, download, share, folders)
      calendar.py        # Google Calendar (events CRUD)
      docs.py            # Google Docs (read, create, append text)
      notion.py          # Notion (pages, databases, blocks)
      whatsapp.py        # WhatsApp (text, images, documents, templates)
      reddit.py          # Reddit (posts, comments, voting, browsing)
      youtube.py         # YouTube (search, upload, manage videos)
      linkedin.py        # LinkedIn (posts, image sharing, profile)
      shopify.py         # Shopify (products, orders, customers, inventory)
      stripe.py          # Stripe (payments, customers, subscriptions, refunds)
      twilio.py          # Twilio (SMS/MMS messaging)
    tools/               # Executable tool plugins (web search, file I/O, etc.)
    memory/
      store.py           # Persistent memory (conversation history + facts)
    cli/
      interface.py       # Interactive REPL & single-shot CLI
```

## Memory System

GOLIATH has a persistent memory system that lets it remember context across tasks and sessions. Data is stored as JSON at `~/.goliath/memory.json`.

**Two layers:**

| Layer | What it does | How it works |
|---|---|---|
| **Conversation history** | Remembers recent tasks and responses | Last 20 turns auto-fed as context to the model |
| **Facts** | Persistent key-value store | Injected into the system prompt every request |

### Memory Commands (Interactive Mode)

| Command | Description |
|---|---|
| `/memory` | Show memory status and file location |
| `/history` | Show conversation history |
| `/remember <key> <value>` | Store a persistent fact |
| `/recall <key>` | Retrieve a stored fact |
| `/forget <key>` | Remove a stored fact |
| `/facts` | List all stored facts |
| `/clear history` | Clear conversation history |
| `/clear all` | Clear all memory (history + facts) |

### Programmatic Usage

```python
from goliath.memory.store import Memory

mem = Memory()

# Conversation history (auto-managed by the engine)
mem.add_turn("user", "What is Python?")
mem.add_turn("assistant", "Python is a programming language.")
history = mem.get_history()

# Facts (persistent key-value pairs)
mem.remember("name", "GOLIATH")
mem.remember("owner", "zdevelops1")
print(mem.recall("name"))        # "GOLIATH"
print(mem.facts())               # {"name": "GOLIATH", "owner": "zdevelops1"}
mem.forget("owner")
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

Twenty-one built-in integrations for connecting GOLIATH to external services:

| Integration | What it does | Setup |
|---|---|---|
| **X / Twitter** | Post tweets, threads, and media | 4 OAuth keys from [developer.x.com](https://developer.x.com) |
| **Instagram** | Post photos, Reels, and carousels | Meta Graph API token ([setup guide](src/goliath/integrations/instagram.py)) |
| **Discord** | Send messages, rich embeds, and files | Webhook URL (no auth needed) |
| **Telegram** | Send messages, photos, and documents | Bot token from [@BotFather](https://t.me/BotFather) |
| **Gmail** | Send emails with HTML and attachments | App password from [Google](https://myaccount.google.com/apppasswords) |
| **Slack** | Send messages, Block Kit, and file uploads | Webhook URL or bot token from [api.slack.com](https://api.slack.com/apps) |
| **GitHub** | Manage repos, issues, PRs, files, and Actions | Personal access token from [github.com/settings/tokens](https://github.com/settings/tokens) |
| **Image Generation** | Generate, edit, and vary images via DALL-E | Uses existing `OPENAI_API_KEY` |
| **Web Scraper** | Extract text, links, and data from URLs | No keys needed |
| **Google Sheets** | Read, write, and manage spreadsheet data | Service account JSON or API key ([setup guide](src/goliath/integrations/sheets.py)) |
| **Google Drive** | Upload, download, share, and manage files | Service account JSON ([setup guide](src/goliath/integrations/drive.py)) |
| **Google Calendar** | List, create, update, and delete events | Service account JSON ([setup guide](src/goliath/integrations/calendar.py)) |
| **Google Docs** | Read, create, and append to documents | Service account JSON ([setup guide](src/goliath/integrations/docs.py)) |
| **Notion** | Manage pages, databases, and blocks | Internal integration token from [notion.so/my-integrations](https://www.notion.so/my-integrations) |
| **WhatsApp** | Send text, images, documents, and templates | Meta Cloud API token ([setup guide](src/goliath/integrations/whatsapp.py)) |
| **Reddit** | Submit posts, comment, vote, and browse | Script app credentials from [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) |
| **YouTube** | Search, upload, and manage videos | API key or OAuth token from [Google Cloud Console](https://console.cloud.google.com/) |
| **LinkedIn** | Share posts, images, and manage profile | OAuth token from [developer.linkedin.com](https://developer.linkedin.com/) |
| **Shopify** | Manage products, orders, customers, and inventory | Admin API token from your [Shopify admin](https://admin.shopify.com/) |
| **Stripe** | Payments, customers, subscriptions, and refunds | Secret key from [dashboard.stripe.com/apikeys](https://dashboard.stripe.com/apikeys) |
| **Twilio SMS** | Send and manage SMS/MMS messages | Account SID + auth token from [console.twilio.com](https://console.twilio.com/) |

### Quick Examples

```python
from goliath.integrations.x import XClient
from goliath.integrations.instagram import InstagramClient
from goliath.integrations.discord import DiscordClient
from goliath.integrations.telegram import TelegramClient
from goliath.integrations.gmail import GmailClient
from goliath.integrations.slack import SlackClient
from goliath.integrations.github import GitHubClient
from goliath.integrations.imagegen import ImageGenClient
from goliath.integrations.scraper import WebScraper
from goliath.integrations.sheets import SheetsClient
from goliath.integrations.drive import DriveClient
from goliath.integrations.calendar import CalendarClient
from goliath.integrations.docs import DocsClient
from goliath.integrations.notion import NotionClient
from goliath.integrations.whatsapp import WhatsAppClient
from goliath.integrations.reddit import RedditClient
from goliath.integrations.youtube import YouTubeClient
from goliath.integrations.linkedin import LinkedInClient
from goliath.integrations.shopify import ShopifyClient
from goliath.integrations.stripe import StripeClient
from goliath.integrations.twilio import TwilioClient

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

# Generate an image from a text prompt
result = ImageGenClient().generate("A futuristic city skyline at sunset")

# Scrape a web page
data = WebScraper().get_text("https://example.com")

# Read from a Google Sheet
rows = SheetsClient().get_values("SPREADSHEET_ID", "Sheet1!A1:D10")

# Upload a file to Google Drive
DriveClient().upload_file("report.pdf", folder_id="FOLDER_ID")

# Create a Google Calendar event
CalendarClient().create_event(summary="Standup", start="2025-06-01T09:00:00", end="2025-06-01T09:30:00")

# Append text to a Google Doc
DocsClient().append_text("DOCUMENT_ID", "\nNew section content here.")

# Search Notion
NotionClient().search("project plan")

# Send a WhatsApp message
WhatsAppClient().send_text(to="15551234567", body="Hello from GOLIATH!")

# Submit a Reddit post
RedditClient().submit_text("test", title="Hello from GOLIATH", text="Automated post!")

# Search YouTube
YouTubeClient().search("Python tutorial", max_results=5)

# Share a LinkedIn post
LinkedInClient().create_post("Hello from GOLIATH!")

# List Shopify products
ShopifyClient().list_products(limit=10)

# Create a Stripe payment intent
StripeClient().create_payment_intent(amount=2000, currency="usd")

# Send an SMS via Twilio
TwilioClient().send(to="+15559876543", body="Hello from GOLIATH!")
```

Each integration file contains full setup instructions in its docstring.

## Safety & Content Moderation

GOLIATH includes a built-in content moderation layer that automatically screens every task before it reaches the AI model. Harmful requests are blocked with a clear `[BLOCKED]` message — nothing is sent to the provider.

**Blocked categories:**

| Category | What it catches |
|---|---|
| **Illegal activity** | Weapons, drugs, hacking, counterfeiting, trafficking |
| **Violence & threats** | Instructions to harm, kill, or assault; covering up violence |
| **Hate speech** | Content targeting groups based on race, religion, gender, orientation |
| **Harassment** | Stalking, doxxing, swatting, blackmail, intimidation |
| **Self-harm** | Suicide methods, self-injury (includes crisis helpline info) |
| **Sexual exploitation** | Any sexual content involving minors |
| **Spam & fraud** | Phishing, scams, impersonation, fake reviews, Ponzi schemes |

```
GOLIATH > how to hack someone's account

[BLOCKED] This request appears to involve illegal activity. GOLIATH cannot assist with this.
```

The moderation module lives at `src/goliath/core/moderation.py` and uses compiled regex patterns for fast screening with minimal latency.

## Security

All API keys and secrets are loaded exclusively from environment variables or a `.env` file — no credentials are hardcoded in source code. The `.env` file is git-ignored and must never be committed.

**Security practices built into GOLIATH:**

- API tokens sent via `Authorization` headers (never in URLs or request bodies)
- URL scheme validation in the web scraper (blocks `file://` and SSRF)
- Input length limits in the CLI (32K characters) and memory commands
- Error messages sanitized to prevent credential leaks
- File handles properly managed to prevent resource leaks

For vulnerability reporting, see [SECURITY.md](SECURITY.md). For community standards and responsible use policies, see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

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

**Memory**

| Variable | Default | Description |
|---|---|---|
| `GOLIATH_MEMORY_PATH` | `~/.goliath/memory.json` | Path to the memory file |
| `GOLIATH_MEMORY_MAX_HISTORY` | `20` | Max conversation turns to keep |

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
| `IMAGEGEN_DEFAULT_MODEL` | DALL-E model (`dall-e-3` default, `dall-e-2`, `gpt-image-1`) |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Path to Google service account JSON (Sheets, Drive, Calendar, Docs) |
| `GOOGLE_SHEETS_API_KEY` | Google API key for read-only Sheets access |
| `NOTION_API_KEY` | Notion internal integration token |
| `WHATSAPP_PHONE_ID` | WhatsApp Business phone number ID |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp Cloud API access token |
| `REDDIT_CLIENT_ID` | Reddit script app client ID |
| `REDDIT_CLIENT_SECRET` | Reddit script app client secret |
| `REDDIT_USERNAME` | Reddit account username |
| `REDDIT_PASSWORD` | Reddit account password |
| `YOUTUBE_API_KEY` | YouTube Data API key (read-only) |
| `YOUTUBE_ACCESS_TOKEN` | YouTube OAuth token (upload/manage) |
| `LINKEDIN_ACCESS_TOKEN` | LinkedIn OAuth access token |
| `LINKEDIN_PERSON_ID` | LinkedIn member person ID |
| `SHOPIFY_STORE` | Shopify store domain (e.g. `your-store.myshopify.com`) |
| `SHOPIFY_ACCESS_TOKEN` | Shopify Admin API access token |
| `STRIPE_SECRET_KEY` | Stripe secret key (`sk_test_` or `sk_live_`) |
| `TWILIO_ACCOUNT_SID` | Twilio Account SID |
| `TWILIO_AUTH_TOKEN` | Twilio Auth Token |
| `TWILIO_PHONE_NUMBER` | Twilio sender phone number (E.164 format) |

## License

MIT

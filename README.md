# GOLIATH

[![CI](https://github.com/zdevelops1/GOLIATH/actions/workflows/ci.yml/badge.svg)](https://github.com/zdevelops1/GOLIATH/actions/workflows/ci.yml)

**Universal AI Automation Engine**

GOLIATH is a modular, plugin-driven automation engine that takes plain-English tasks and executes them through AI. Built on the xAI Grok API by default, with drop-in support for 8 additional model providers and 67 third-party integrations. Any model provider or integration can be added as a plugin with zero changes to the core.

## Supported Providers

| Provider | Status | Default Model | Plugin File |
|---|---|---|---|
| **xAI Grok** | Default | `grok-3-latest` | `models/grok.py` |
| **OpenAI** | Ready | `gpt-4o` | `models/openai_provider.py` |
| **Anthropic Claude** | Ready | `claude-sonnet-4-5-20250929` | `models/claude.py` |
| **Google Gemini** | Ready | `gemini-2.0-flash` | `models/gemini.py` |
| **Mistral AI** | Ready | `mistral-large-latest` | `models/mistral.py` |
| **DeepSeek** | Ready | `deepseek-chat` | `models/deepseek.py` |
| **Ollama (local)** | Ready | `llama3.1` | `models/ollama.py` |
| **Cohere** | Ready | `command-r-plus` | `models/cohere.py` |
| **Perplexity** | Ready | `sonar-pro` | `models/perplexity.py` |

All nine providers are built in. Add the API key and go — no code changes needed. Ollama runs locally and needs no API key.

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
MISTRAL_API_KEY=your-mistral-key-here
DEEPSEEK_API_KEY=your-deepseek-key-here
COHERE_API_KEY=your-cohere-key-here
PERPLEXITY_API_KEY=your-perplexity-key-here
# Ollama — no key needed, just install and run: ollama serve
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

Options: `grok` (default), `openai`, `claude`, `gemini`, `mistral`, `deepseek`, `ollama`, `cohere`, `perplexity`

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
      mistral.py         # Mistral AI provider (Large, Medium, Codestral)
      deepseek.py        # DeepSeek provider (Chat, Reasoner)
      ollama.py          # Ollama provider (local Llama, Mistral, Phi, etc.)
      cohere.py          # Cohere provider (Command R+, Command R)
      perplexity.py      # Perplexity provider (Sonar, Sonar Pro)
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
      pinterest.py       # Pinterest (pins, boards, search)
      tiktok.py          # TikTok (video publishing, comments)
      spotify.py         # Spotify (search, playlists, playback)
      zoom.py            # Zoom (meetings CRUD, participants)
      calendly.py        # Calendly (event types, scheduled events, invitees)
      hubspot.py         # HubSpot (contacts, deals, companies)
      salesforce.py      # Salesforce (SOQL queries, SObject CRUD)
      wordpress.py       # WordPress (posts, pages, media)
      webflow.py         # Webflow (sites, CMS collections, items)
      paypal.py          # PayPal (orders, payments, payouts, refunds)
      dropbox.py         # Dropbox (files, folders, sharing, search)
      jira.py            # Jira (issues, transitions, comments, JQL search)
      airtable.py        # Airtable (bases, tables, records, formulas)
      mailchimp.py       # Mailchimp (audiences, subscribers, campaigns)
      sendgrid.py        # SendGrid (transactional email, templates, contacts)
      trello.py          # Trello (boards, lists, cards, checklists)
      s3.py              # Amazon S3 (objects, buckets, presigned URLs)
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

Sixty-seven built-in integrations for connecting GOLIATH to external services:

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
| **Pinterest** | Create pins, manage boards, and search | OAuth token from [developers.pinterest.com](https://developers.pinterest.com/) |
| **TikTok** | Publish videos and manage content | OAuth token from [developers.tiktok.com](https://developers.tiktok.com/) |
| **Spotify** | Search music, manage playlists, control playback | Client credentials or OAuth from [developer.spotify.com](https://developer.spotify.com/) |
| **Zoom** | Create and manage meetings | Server-to-Server OAuth or token from [marketplace.zoom.us](https://marketplace.zoom.us/) |
| **Calendly** | Manage event types, events, and invitees | Personal access token from [calendly.com](https://calendly.com/integrations/api_webhooks) |
| **HubSpot** | CRM contacts, deals, and companies | Private app token from [app.hubspot.com](https://app.hubspot.com/) |
| **Salesforce** | CRM queries, SObject CRUD | OAuth token or password flow from [Salesforce Setup](https://login.salesforce.com/) |
| **WordPress** | Manage posts, pages, and media | Application password from your WordPress admin |
| **Webflow** | Manage sites, CMS collections, and items | API token from [webflow.com](https://webflow.com/) |
| **PayPal** | Orders, payments, payouts, and refunds | REST API credentials from [developer.paypal.com](https://developer.paypal.com/) |
| **Dropbox** | Upload, download, manage files and folders | Access token from [dropbox.com/developers](https://www.dropbox.com/developers/apps) |
| **Jira** | Issues, transitions, comments, JQL search | API token from [id.atlassian.com](https://id.atlassian.com/manage-profile/security/api-tokens) |
| **Airtable** | Bases, tables, records, and formulas | Personal access token from [airtable.com/create/tokens](https://airtable.com/create/tokens) |
| **Mailchimp** | Audiences, subscribers, and campaigns | API key from [mailchimp.com](https://us1.admin.mailchimp.com/account/api/) |
| **SendGrid** | Transactional email, templates, contacts | API key from [app.sendgrid.com](https://app.sendgrid.com/settings/api_keys) |
| **Trello** | Boards, lists, cards, and checklists | API key + token from [trello.com/power-ups/admin](https://trello.com/power-ups/admin) |
| **Amazon S3** | Object storage, buckets, presigned URLs | AWS credentials from [IAM Console](https://console.aws.amazon.com/iam/) |
| **Asana** | Projects, tasks, workspaces, and comments | Personal access token from [app.asana.com](https://app.asana.com/0/developer-console) |
| **Monday.com** | Boards, items, updates via GraphQL | API token from [monday.com/apps/manage](https://monday.com/apps/manage) |
| **Zendesk** | Tickets, users, organizations, and search | API token from [Zendesk Admin](https://support.zendesk.com/hc/en-us/articles/4408889192858) |
| **Intercom** | Contacts, conversations, and messaging | Access token from [Intercom Developer Hub](https://app.intercom.com/) |
| **Twitch** | Channels, streams, chat, and clips | Client credentials from [dev.twitch.tv](https://dev.twitch.tv/console) |
| **Snapchat** | Campaigns, ad squads, and creative media | OAuth token from [Snapchat Marketing API](https://business.snapchat.com/) |
| **Medium** | Publish posts and manage publications | Integration token from [Medium settings](https://medium.com/me/settings/security) |
| **Substack** | Draft, publish, and manage newsletter posts | Session cookie from [substack.com](https://substack.com/) |
| **Cloudflare** | DNS records, zones, Workers, and caching | API token from [Cloudflare dashboard](https://dash.cloudflare.com/profile/api-tokens) |
| **Firebase** | Firestore, Realtime Database, and Auth | Project config from [Firebase console](https://console.firebase.google.com/) |
| **Figma** | Files, components, comments, and image exports | Personal access token from [Figma settings](https://www.figma.com/developers/api#access-tokens) |
| **Canva** | Designs, folders, exports, and brand templates | OAuth token from [Canva Developer Portal](https://www.canva.com/developers/) |
| **Loom** | Videos, transcripts, folders, and embeds | Access token from [Loom Developer settings](https://www.loom.com/account/developer) |
| **Typeform** | Forms, responses, workspaces, and insights | Personal token from [Typeform admin](https://admin.typeform.com/account#/section/tokens) |
| **Beehiiv** | Newsletter posts, subscribers, and publication stats | API key from [Beehiiv settings](https://app.beehiiv.com/) |
| **ConvertKit** | Subscribers, forms, sequences, and broadcasts | API key + secret from [ConvertKit settings](https://app.convertkit.com/account_settings/advanced_settings) |
| **Linear** | Issues, projects, teams, and comments via GraphQL | API key from [Linear settings](https://linear.app/settings/api) |
| **Resend** | Transactional email, domains, and batch sending | API key from [resend.com](https://resend.com/api-keys) |
| **Supabase** | Database CRUD, storage, and auth | Project URL + key from [Supabase dashboard](https://supabase.com/) |
| **Notion AI** | Text generation, summarization, translation, grammar | Integration token from [notion.so/my-integrations](https://www.notion.so/my-integrations) |
| **Perplexity Search** | AI-powered web search with citations | API key from [perplexity.ai](https://www.perplexity.ai/settings/api) |
| **Brave Search** | Web, news, and image search with summarization | API key from [brave.com/search/api](https://brave.com/search/api/) |
| **Wikipedia** | Articles, summaries, search, on-this-day | No API key required (free) |
| **Weather (OpenWeatherMap)** | Current weather, forecasts, air quality, geocoding | API key from [openweathermap.org](https://openweathermap.org/) |
| **News API** | Headlines, article search, and news sources | API key from [newsapi.org](https://newsapi.org/) |
| **Google Maps** | Geocoding, places, directions, distance matrix | API key from [Google Cloud Console](https://console.cloud.google.com/) |
| **Yelp** | Business search, reviews, and categories | API key from [yelp.com/developers](https://www.yelp.com/developers/) |
| **OpenSea** | NFT collections, assets, events, and offers | API key from [opensea.io](https://docs.opensea.io/) |
| **Binance** | Crypto market data, order books, klines, account info | API key from [binance.com](https://www.binance.com/) |

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
from goliath.integrations.pinterest import PinterestClient
from goliath.integrations.tiktok import TikTokClient
from goliath.integrations.spotify import SpotifyClient
from goliath.integrations.zoom import ZoomClient
from goliath.integrations.calendly import CalendlyClient
from goliath.integrations.hubspot import HubSpotClient
from goliath.integrations.salesforce import SalesforceClient
from goliath.integrations.wordpress import WordPressClient
from goliath.integrations.webflow import WebflowClient
from goliath.integrations.paypal import PayPalClient
from goliath.integrations.dropbox import DropboxClient
from goliath.integrations.jira import JiraClient
from goliath.integrations.airtable import AirtableClient
from goliath.integrations.mailchimp import MailchimpClient
from goliath.integrations.sendgrid import SendGridClient
from goliath.integrations.trello import TrelloClient
from goliath.integrations.s3 import S3Client
from goliath.integrations.asana import AsanaClient
from goliath.integrations.monday import MondayClient
from goliath.integrations.zendesk import ZendeskClient
from goliath.integrations.intercom import IntercomClient
from goliath.integrations.twitch import TwitchClient
from goliath.integrations.snapchat import SnapchatClient
from goliath.integrations.medium import MediumClient
from goliath.integrations.substack import SubstackClient
from goliath.integrations.cloudflare import CloudflareClient
from goliath.integrations.firebase import FirebaseClient
from goliath.integrations.figma import FigmaClient
from goliath.integrations.canva import CanvaClient
from goliath.integrations.loom import LoomClient
from goliath.integrations.typeform import TypeformClient
from goliath.integrations.beehiiv import BeehiivClient
from goliath.integrations.convertkit import ConvertKitClient
from goliath.integrations.linear import LinearClient
from goliath.integrations.resend import ResendClient
from goliath.integrations.supabase import SupabaseClient
from goliath.integrations.notion_ai import NotionAIClient
from goliath.integrations.perplexity_search import PerplexitySearchClient
from goliath.integrations.brave_search import BraveSearchClient
from goliath.integrations.wikipedia import WikipediaClient
from goliath.integrations.weather import WeatherClient
from goliath.integrations.news import NewsClient
from goliath.integrations.google_maps import GoogleMapsClient
from goliath.integrations.yelp import YelpClient
from goliath.integrations.opensea import OpenSeaClient
from goliath.integrations.binance import BinanceClient

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

# Create a Pinterest pin
PinterestClient().create_pin(board_id="123", title="My Pin", image_url="https://example.com/photo.jpg")

# Publish a TikTok video from URL
TikTokClient().publish_video_from_url(video_url="https://example.com/video.mp4", title="Automated TikTok")

# Search Spotify tracks
SpotifyClient().search("Bohemian Rhapsody", search_type="track")

# Create a Zoom meeting
ZoomClient().create_meeting(topic="Team Standup", duration=30)

# List Calendly scheduled events
CalendlyClient().list_scheduled_events()

# Create a HubSpot contact
HubSpotClient().create_contact(properties={"email": "jane@example.com", "firstname": "Jane"})

# Query Salesforce contacts
SalesforceClient().query("SELECT Id, Name FROM Contact LIMIT 10")

# Create a WordPress post
WordPressClient().create_post(title="Hello World", content="<p>Automated post!</p>")

# Create a Webflow CMS item
WebflowClient().create_item(collection_id="col_abc", fields={"name": "New Post", "slug": "new-post"})

# Create a PayPal order
PayPalClient().create_order(amount="29.99", currency="USD")

# List Dropbox files
DropboxClient().list_folder("/Documents")

# Create a Jira issue
JiraClient().create_issue(project="PROJ", summary="Bug report", issue_type="Bug")

# List Airtable records
AirtableClient().list_records(base_id="appXXX", table="Tasks")

# Add a Mailchimp subscriber
MailchimpClient().add_subscriber(list_id="abc123", email="user@example.com")

# Send an email via SendGrid
SendGridClient().send(to="user@example.com", subject="Hello", text="Hello from GOLIATH!")

# Create a Trello card
TrelloClient().create_card(list_id="xyz789", name="New task")

# Upload a file to S3
S3Client().upload_file("report.pdf", "my-bucket", "reports/report.pdf")

# Create an Asana task
AsanaClient().create_task(project_gid="12345", name="Build landing page", notes="Design and implement.")

# Create a Monday.com item
MondayClient().create_item(board_id="67890", item_name="New feature request")

# Create a Zendesk ticket
ZendeskClient().create_ticket(subject="Cannot log in", description="User reports 403 error.", priority="high")

# Send an Intercom message
IntercomClient().send_message(from_admin_id="admin_1", to_contact_id="user_1", body="How can we help?")

# Search Twitch channels
TwitchClient().search_channels("speedrunning")

# List Snapchat campaigns
SnapchatClient().list_campaigns()

# Publish a Medium post
MediumClient().create_post(title="My Article", content="# Hello World", content_format="markdown")

# Create a Substack draft
SubstackClient().create_draft(title="Weekly Digest", body_html="<h1>Hello Subscribers</h1>")

# Create a Cloudflare DNS record
CloudflareClient().create_dns_record(zone_id="z1", type="A", name="app.example.com", content="192.0.2.1")

# Set a Firebase Firestore document
FirebaseClient().set_document("users", "user123", {"name": "Jane", "email": "jane@example.com"})

# Export a Figma frame as PNG
FigmaClient().export_images("FILE_KEY", node_ids=["1:2"], format="png", scale=2)

# List Canva designs
CanvaClient().list_designs()

# Get a Loom video transcript
LoomClient().get_transcript("VIDEO_ID")

# Get Typeform responses
TypeformClient().get_responses("FORM_ID", page_size=25)

# Create a Beehiiv newsletter post
BeehiivClient().create_post(title="Weekly Newsletter", content_html="<p>Hello readers!</p>")

# Add a ConvertKit subscriber to a form
ConvertKitClient().add_subscriber_to_form(form_id=12345, email="reader@example.com")

# Create a Linear issue
LinearClient().create_issue(team_id="TEAM_UUID", title="Fix login bug", priority=2)

# Send an email via Resend
ResendClient().send(from_addr="you@yourdomain.com", to=["user@example.com"], subject="Hello", html="<p>Hi!</p>")

# Query Supabase rows
SupabaseClient().select("users", columns="id,name,email", limit=10)

# Generate text with Notion AI
NotionAIClient().generate(prompt="Write a product launch announcement for a new AI tool.")

# AI-powered web search with Perplexity
PerplexitySearchClient().search("What is the current price of Bitcoin?")

# Web search with Brave Search
BraveSearchClient().web_search("Python asyncio tutorial", count=5)

# Search Wikipedia articles
WikipediaClient().search("artificial intelligence")

# Get current weather
WeatherClient().get_current("London", units="metric")

# Search news headlines
NewsClient().top_headlines(country="us", category="technology")

# Geocode an address with Google Maps
GoogleMapsClient().geocode("1600 Amphitheatre Parkway, Mountain View, CA")

# Search Yelp businesses
YelpClient().search("coffee", location="San Francisco, CA")

# Get an NFT collection from OpenSea
OpenSeaClient().get_collection("boredapeyachtclub")

# Get Bitcoin price from Binance
BinanceClient().get_price("BTCUSDT")
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
| `MISTRAL_API_KEY` | — | Mistral AI API key |
| `MISTRAL_DEFAULT_MODEL` | `mistral-large-latest` | Mistral model |
| `DEEPSEEK_API_KEY` | — | DeepSeek API key |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | DeepSeek API base URL |
| `DEEPSEEK_DEFAULT_MODEL` | `deepseek-chat` | DeepSeek model |
| `OLLAMA_BASE_URL` | `http://localhost:11434/v1` | Ollama server URL |
| `OLLAMA_DEFAULT_MODEL` | `llama3.1` | Ollama model name |
| `COHERE_API_KEY` | — | Cohere API key |
| `COHERE_DEFAULT_MODEL` | `command-r-plus` | Cohere model |
| `PERPLEXITY_API_KEY` | — | Perplexity API key |
| `PERPLEXITY_BASE_URL` | `https://api.perplexity.ai` | Perplexity API base URL |
| `PERPLEXITY_DEFAULT_MODEL` | `sonar-pro` | Perplexity model |

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
| `PINTEREST_ACCESS_TOKEN` | Pinterest OAuth access token |
| `TIKTOK_ACCESS_TOKEN` | TikTok OAuth access token |
| `SPOTIFY_CLIENT_ID` | Spotify app client ID |
| `SPOTIFY_CLIENT_SECRET` | Spotify app client secret |
| `SPOTIFY_ACCESS_TOKEN` | Spotify user OAuth token (optional, for playlists/playback) |
| `ZOOM_ACCOUNT_ID` | Zoom Server-to-Server OAuth account ID |
| `ZOOM_CLIENT_ID` | Zoom app client ID |
| `ZOOM_CLIENT_SECRET` | Zoom app client secret |
| `ZOOM_ACCESS_TOKEN` | Zoom user OAuth token (alternative to S2S) |
| `CALENDLY_ACCESS_TOKEN` | Calendly personal access token |
| `HUBSPOT_ACCESS_TOKEN` | HubSpot private app access token |
| `SALESFORCE_INSTANCE_URL` | Salesforce instance URL |
| `SALESFORCE_ACCESS_TOKEN` | Salesforce OAuth access token |
| `SALESFORCE_CLIENT_ID` | Salesforce Connected App client ID |
| `SALESFORCE_CLIENT_SECRET` | Salesforce Connected App client secret |
| `SALESFORCE_USERNAME` | Salesforce username (password flow) |
| `SALESFORCE_PASSWORD` | Salesforce password + security token (password flow) |
| `WORDPRESS_URL` | WordPress site URL (e.g. `https://your-site.com`) |
| `WORDPRESS_USERNAME` | WordPress username |
| `WORDPRESS_APP_PASSWORD` | WordPress application password |
| `WEBFLOW_ACCESS_TOKEN` | Webflow API access token |
| `PAYPAL_CLIENT_ID` | PayPal REST API client ID |
| `PAYPAL_CLIENT_SECRET` | PayPal REST API client secret |
| `PAYPAL_SANDBOX` | `true` for sandbox, `false` for live (default: `true`) |
| `DROPBOX_ACCESS_TOKEN` | Dropbox access token |
| `JIRA_URL` | Jira Cloud URL (e.g. `https://your-domain.atlassian.net`) |
| `JIRA_EMAIL` | Atlassian account email |
| `JIRA_API_TOKEN` | Jira API token |
| `AIRTABLE_ACCESS_TOKEN` | Airtable personal access token |
| `MAILCHIMP_API_KEY` | Mailchimp API key (e.g. `xxx-us14`) |
| `MAILCHIMP_SERVER_PREFIX` | Mailchimp data center (e.g. `us14`) |
| `SENDGRID_API_KEY` | SendGrid API key (starts with `SG.`) |
| `SENDGRID_FROM_EMAIL` | Verified sender email for SendGrid |
| `TRELLO_API_KEY` | Trello API key |
| `TRELLO_TOKEN` | Trello authorization token |
| `AWS_ACCESS_KEY_ID` | AWS access key ID |
| `AWS_SECRET_ACCESS_KEY` | AWS secret access key |
| `AWS_DEFAULT_REGION` | AWS region (default: `us-east-1`) |
| `AWS_S3_BUCKET` | Default S3 bucket name (optional) |
| `ASANA_ACCESS_TOKEN` | Asana personal access token |
| `MONDAY_API_TOKEN` | Monday.com API token |
| `ZENDESK_SUBDOMAIN` | Zendesk subdomain |
| `ZENDESK_EMAIL` | Zendesk account email |
| `ZENDESK_API_TOKEN` | Zendesk API token |
| `INTERCOM_ACCESS_TOKEN` | Intercom access token |
| `TWITCH_CLIENT_ID` | Twitch app client ID |
| `TWITCH_CLIENT_SECRET` | Twitch app client secret |
| `TWITCH_ACCESS_TOKEN` | Twitch OAuth token (optional) |
| `SNAPCHAT_ACCESS_TOKEN` | Snapchat Marketing API token |
| `SNAPCHAT_AD_ACCOUNT_ID` | Snapchat ad account ID |
| `MEDIUM_ACCESS_TOKEN` | Medium integration token |
| `SUBSTACK_SUBDOMAIN` | Substack publication subdomain |
| `SUBSTACK_SESSION_COOKIE` | Substack session cookie |
| `SUBSTACK_USER_ID` | Substack user ID |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API token |
| `CLOUDFLARE_API_KEY` | Cloudflare Global API key (alternative) |
| `CLOUDFLARE_EMAIL` | Cloudflare account email (with Global key) |
| `FIREBASE_PROJECT_ID` | Firebase project ID |
| `FIREBASE_API_KEY` | Firebase Web API key |
| `FIREBASE_DATABASE_URL` | Firebase Realtime Database URL |
| `FIGMA_ACCESS_TOKEN` | Figma personal access token |
| `CANVA_ACCESS_TOKEN` | Canva OAuth access token |
| `LOOM_ACCESS_TOKEN` | Loom API access token |
| `TYPEFORM_ACCESS_TOKEN` | Typeform personal token |
| `BEEHIIV_API_KEY` | Beehiiv API key |
| `BEEHIIV_PUBLICATION_ID` | Beehiiv publication ID |
| `CONVERTKIT_API_KEY` | ConvertKit API key |
| `CONVERTKIT_API_SECRET` | ConvertKit API secret |
| `LINEAR_API_KEY` | Linear API key |
| `RESEND_API_KEY` | Resend API key |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase anon/service key |
| `NOTION_AI_API_KEY` | Notion AI API key (reuses `NOTION_API_KEY` if set) |
| `BRAVE_SEARCH_API_KEY` | Brave Search subscription token |
| `WIKIPEDIA_ACCESS_TOKEN` | Wikipedia access token (optional — free without) |
| `OPENWEATHER_API_KEY` | OpenWeatherMap API key |
| `NEWS_API_KEY` | NewsAPI.org API key |
| `GOOGLE_MAPS_API_KEY` | Google Maps Platform API key |
| `YELP_API_KEY` | Yelp Fusion API key |
| `OPENSEA_API_KEY` | OpenSea API key |
| `BINANCE_API_KEY` | Binance API key |
| `BINANCE_API_SECRET` | Binance API secret |

## License

MIT

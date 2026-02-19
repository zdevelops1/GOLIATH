"""
GOLIATH Configuration

Central configuration for API keys, model settings, and runtime options.
All secrets are loaded from a .env file (never commit secrets to source).
"""

import os
from pathlib import Path

# Load .env file from the current working directory (project root)
_env_path = Path.cwd() / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


# --- xAI / Grok API ---
XAI_API_KEY = os.environ.get("XAI_API_KEY", "")
XAI_BASE_URL = os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1")
XAI_DEFAULT_MODEL = os.environ.get("XAI_DEFAULT_MODEL", "grok-3-latest")

# --- OpenAI API ---
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_DEFAULT_MODEL = os.environ.get("OPENAI_DEFAULT_MODEL", "gpt-4o")

# --- Anthropic / Claude API ---
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_DEFAULT_MODEL = os.environ.get(
    "ANTHROPIC_DEFAULT_MODEL", "claude-sonnet-4-5-20250929"
)

# --- Google / Gemini API ---
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
GOOGLE_DEFAULT_MODEL = os.environ.get("GOOGLE_DEFAULT_MODEL", "gemini-2.0-flash")

# --- Mistral AI API ---
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY", "")
MISTRAL_DEFAULT_MODEL = os.environ.get("MISTRAL_DEFAULT_MODEL", "mistral-large-latest")

# --- DeepSeek API ---
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_DEFAULT_MODEL = os.environ.get("DEEPSEEK_DEFAULT_MODEL", "deepseek-chat")

# --- Ollama (local models) ---
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_DEFAULT_MODEL = os.environ.get("OLLAMA_DEFAULT_MODEL", "llama3.1")

# --- Cohere API ---
COHERE_API_KEY = os.environ.get("COHERE_API_KEY", "")
COHERE_DEFAULT_MODEL = os.environ.get("COHERE_DEFAULT_MODEL", "command-r-plus")

# --- Perplexity API ---
PERPLEXITY_API_KEY = os.environ.get("PERPLEXITY_API_KEY", "")
PERPLEXITY_BASE_URL = os.environ.get("PERPLEXITY_BASE_URL", "https://api.perplexity.ai")
PERPLEXITY_DEFAULT_MODEL = os.environ.get("PERPLEXITY_DEFAULT_MODEL", "sonar-pro")

# --- X / Twitter API ---
X_CONSUMER_KEY = os.environ.get("X_CONSUMER_KEY", "")
X_CONSUMER_SECRET = os.environ.get("X_CONSUMER_SECRET", "")
X_ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN", "")
X_ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET", "")

# --- Instagram Graph API ---
INSTAGRAM_USER_ID = os.environ.get("INSTAGRAM_USER_ID", "")
INSTAGRAM_ACCESS_TOKEN = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")

# --- Discord ---
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL", "")

# --- Telegram ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# --- Gmail ---
GMAIL_ADDRESS = os.environ.get("GMAIL_ADDRESS", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

# --- Slack ---
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")

# --- GitHub ---
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
GITHUB_OWNER = os.environ.get("GITHUB_OWNER", "")

# --- Image Generation ---
IMAGEGEN_DEFAULT_MODEL = os.environ.get("IMAGEGEN_DEFAULT_MODEL", "dall-e-3")

# --- Google Workspace (Sheets, Drive, Calendar, Docs) ---
GOOGLE_SERVICE_ACCOUNT_FILE = os.environ.get("GOOGLE_SERVICE_ACCOUNT_FILE", "")
GOOGLE_SHEETS_API_KEY = os.environ.get("GOOGLE_SHEETS_API_KEY", "")

# --- Notion ---
NOTION_API_KEY = os.environ.get("NOTION_API_KEY", "")

# --- WhatsApp (Meta Cloud API) ---
WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID", "")
WHATSAPP_ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "")

# --- Reddit ---
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")
REDDIT_USERNAME = os.environ.get("REDDIT_USERNAME", "")
REDDIT_PASSWORD = os.environ.get("REDDIT_PASSWORD", "")

# --- YouTube ---
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
YOUTUBE_ACCESS_TOKEN = os.environ.get("YOUTUBE_ACCESS_TOKEN", "")

# --- LinkedIn ---
LINKEDIN_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_PERSON_ID = os.environ.get("LINKEDIN_PERSON_ID", "")

# --- Shopify ---
SHOPIFY_STORE = os.environ.get("SHOPIFY_STORE", "")
SHOPIFY_ACCESS_TOKEN = os.environ.get("SHOPIFY_ACCESS_TOKEN", "")

# --- Stripe ---
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")

# --- Twilio ---
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "")

# --- Pinterest ---
PINTEREST_ACCESS_TOKEN = os.environ.get("PINTEREST_ACCESS_TOKEN", "")

# --- TikTok ---
TIKTOK_ACCESS_TOKEN = os.environ.get("TIKTOK_ACCESS_TOKEN", "")

# --- Spotify ---
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
SPOTIFY_ACCESS_TOKEN = os.environ.get("SPOTIFY_ACCESS_TOKEN", "")

# --- Zoom ---
ZOOM_ACCOUNT_ID = os.environ.get("ZOOM_ACCOUNT_ID", "")
ZOOM_CLIENT_ID = os.environ.get("ZOOM_CLIENT_ID", "")
ZOOM_CLIENT_SECRET = os.environ.get("ZOOM_CLIENT_SECRET", "")
ZOOM_ACCESS_TOKEN = os.environ.get("ZOOM_ACCESS_TOKEN", "")

# --- Calendly ---
CALENDLY_ACCESS_TOKEN = os.environ.get("CALENDLY_ACCESS_TOKEN", "")

# --- HubSpot ---
HUBSPOT_ACCESS_TOKEN = os.environ.get("HUBSPOT_ACCESS_TOKEN", "")

# --- Salesforce ---
SALESFORCE_INSTANCE_URL = os.environ.get("SALESFORCE_INSTANCE_URL", "")
SALESFORCE_ACCESS_TOKEN = os.environ.get("SALESFORCE_ACCESS_TOKEN", "")
SALESFORCE_CLIENT_ID = os.environ.get("SALESFORCE_CLIENT_ID", "")
SALESFORCE_CLIENT_SECRET = os.environ.get("SALESFORCE_CLIENT_SECRET", "")
SALESFORCE_USERNAME = os.environ.get("SALESFORCE_USERNAME", "")
SALESFORCE_PASSWORD = os.environ.get("SALESFORCE_PASSWORD", "")

# --- WordPress ---
WORDPRESS_URL = os.environ.get("WORDPRESS_URL", "")
WORDPRESS_USERNAME = os.environ.get("WORDPRESS_USERNAME", "")
WORDPRESS_APP_PASSWORD = os.environ.get("WORDPRESS_APP_PASSWORD", "")

# --- Webflow ---
WEBFLOW_ACCESS_TOKEN = os.environ.get("WEBFLOW_ACCESS_TOKEN", "")

# --- PayPal ---
PAYPAL_CLIENT_ID = os.environ.get("PAYPAL_CLIENT_ID", "")
PAYPAL_CLIENT_SECRET = os.environ.get("PAYPAL_CLIENT_SECRET", "")
PAYPAL_SANDBOX = os.environ.get("PAYPAL_SANDBOX", "true")

# --- Dropbox ---
DROPBOX_ACCESS_TOKEN = os.environ.get("DROPBOX_ACCESS_TOKEN", "")

# --- Jira ---
JIRA_URL = os.environ.get("JIRA_URL", "")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")

# --- Airtable ---
AIRTABLE_ACCESS_TOKEN = os.environ.get("AIRTABLE_ACCESS_TOKEN", "")

# --- Mailchimp ---
MAILCHIMP_API_KEY = os.environ.get("MAILCHIMP_API_KEY", "")
MAILCHIMP_SERVER_PREFIX = os.environ.get("MAILCHIMP_SERVER_PREFIX", "")

# --- SendGrid ---
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
SENDGRID_FROM_EMAIL = os.environ.get("SENDGRID_FROM_EMAIL", "")

# --- Trello ---
TRELLO_API_KEY = os.environ.get("TRELLO_API_KEY", "")
TRELLO_TOKEN = os.environ.get("TRELLO_TOKEN", "")

# --- Amazon S3 ---
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
AWS_S3_BUCKET = os.environ.get("AWS_S3_BUCKET", "")
AWS_S3_USE_INSTANCE_PROFILE = (
    os.environ.get("AWS_S3_USE_INSTANCE_PROFILE", "").lower() == "true"
)

# --- Memory ---
MEMORY_PATH = os.environ.get(
    "GOLIATH_MEMORY_PATH", str(Path.home() / ".goliath" / "memory.json")
)
MEMORY_MAX_HISTORY = int(os.environ.get("GOLIATH_MEMORY_MAX_HISTORY", "20"))

# --- Model defaults ---
DEFAULT_PROVIDER = os.environ.get("DEFAULT_PROVIDER", "grok")
MAX_TOKENS = 4096
TEMPERATURE = 0.7

# --- System prompt fed to every task ---
SYSTEM_PROMPT = (
    "You are GOLIATH, a universal AI automation engine. "
    "When given a task, respond with a clear, actionable answer. "
    "If the task requires multiple steps, break it down. "
    "Be concise and precise."
)

# --- Plugin registry ---
# Maps provider names to their module paths for dynamic loading.
# Add new model providers here as they are built.
MODEL_PROVIDERS = {
    "grok": "goliath.models.grok",
    "openai": "goliath.models.openai_provider",
    "claude": "goliath.models.claude",
    "gemini": "goliath.models.gemini",
    "mistral": "goliath.models.mistral",
    "deepseek": "goliath.models.deepseek",
    "ollama": "goliath.models.ollama",
    "cohere": "goliath.models.cohere",
    "perplexity": "goliath.models.perplexity",
}

# --- Integration registry ---
# Maps integration names to their module paths.
# Add new third-party integrations here.
INTEGRATIONS = {
    "x": "goliath.integrations.x",
    "instagram": "goliath.integrations.instagram",
    "discord": "goliath.integrations.discord",
    "telegram": "goliath.integrations.telegram",
    "gmail": "goliath.integrations.gmail",
    "scraper": "goliath.integrations.scraper",
    "slack": "goliath.integrations.slack",
    "github": "goliath.integrations.github",
    "imagegen": "goliath.integrations.imagegen",
    "sheets": "goliath.integrations.sheets",
    "drive": "goliath.integrations.drive",
    "calendar": "goliath.integrations.calendar",
    "docs": "goliath.integrations.docs",
    "notion": "goliath.integrations.notion",
    "whatsapp": "goliath.integrations.whatsapp",
    "reddit": "goliath.integrations.reddit",
    "youtube": "goliath.integrations.youtube",
    "linkedin": "goliath.integrations.linkedin",
    "shopify": "goliath.integrations.shopify",
    "stripe": "goliath.integrations.stripe",
    "twilio": "goliath.integrations.twilio",
    "pinterest": "goliath.integrations.pinterest",
    "tiktok": "goliath.integrations.tiktok",
    "spotify": "goliath.integrations.spotify",
    "zoom": "goliath.integrations.zoom",
    "calendly": "goliath.integrations.calendly",
    "hubspot": "goliath.integrations.hubspot",
    "salesforce": "goliath.integrations.salesforce",
    "wordpress": "goliath.integrations.wordpress",
    "webflow": "goliath.integrations.webflow",
    "paypal": "goliath.integrations.paypal",
    "dropbox": "goliath.integrations.dropbox",
    "jira": "goliath.integrations.jira",
    "airtable": "goliath.integrations.airtable",
    "mailchimp": "goliath.integrations.mailchimp",
    "sendgrid": "goliath.integrations.sendgrid",
    "trello": "goliath.integrations.trello",
    "s3": "goliath.integrations.s3",
}

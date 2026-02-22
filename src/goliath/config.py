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

# --- Asana ---
ASANA_ACCESS_TOKEN = os.environ.get("ASANA_ACCESS_TOKEN", "")

# --- Monday.com ---
MONDAY_API_TOKEN = os.environ.get("MONDAY_API_TOKEN", "")

# --- Zendesk ---
ZENDESK_SUBDOMAIN = os.environ.get("ZENDESK_SUBDOMAIN", "")
ZENDESK_EMAIL = os.environ.get("ZENDESK_EMAIL", "")
ZENDESK_API_TOKEN = os.environ.get("ZENDESK_API_TOKEN", "")

# --- Intercom ---
INTERCOM_ACCESS_TOKEN = os.environ.get("INTERCOM_ACCESS_TOKEN", "")

# --- Twitch ---
TWITCH_CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID", "")
TWITCH_CLIENT_SECRET = os.environ.get("TWITCH_CLIENT_SECRET", "")
TWITCH_ACCESS_TOKEN = os.environ.get("TWITCH_ACCESS_TOKEN", "")

# --- Snapchat ---
SNAPCHAT_ACCESS_TOKEN = os.environ.get("SNAPCHAT_ACCESS_TOKEN", "")
SNAPCHAT_AD_ACCOUNT_ID = os.environ.get("SNAPCHAT_AD_ACCOUNT_ID", "")

# --- Medium ---
MEDIUM_ACCESS_TOKEN = os.environ.get("MEDIUM_ACCESS_TOKEN", "")

# --- Substack ---
SUBSTACK_SUBDOMAIN = os.environ.get("SUBSTACK_SUBDOMAIN", "")
SUBSTACK_SESSION_COOKIE = os.environ.get("SUBSTACK_SESSION_COOKIE", "")
SUBSTACK_USER_ID = os.environ.get("SUBSTACK_USER_ID", "")

# --- Cloudflare ---
CLOUDFLARE_API_TOKEN = os.environ.get("CLOUDFLARE_API_TOKEN", "")
CLOUDFLARE_API_KEY = os.environ.get("CLOUDFLARE_API_KEY", "")
CLOUDFLARE_EMAIL = os.environ.get("CLOUDFLARE_EMAIL", "")

# --- Firebase ---
FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "")
FIREBASE_API_KEY = os.environ.get("FIREBASE_API_KEY", "")
FIREBASE_DATABASE_URL = os.environ.get("FIREBASE_DATABASE_URL", "")
FIREBASE_SERVICE_ACCOUNT_FILE = os.environ.get("FIREBASE_SERVICE_ACCOUNT_FILE", "")

# --- Figma ---
FIGMA_ACCESS_TOKEN = os.environ.get("FIGMA_ACCESS_TOKEN", "")

# --- Canva ---
CANVA_ACCESS_TOKEN = os.environ.get("CANVA_ACCESS_TOKEN", "")

# --- Loom ---
LOOM_ACCESS_TOKEN = os.environ.get("LOOM_ACCESS_TOKEN", "")

# --- Typeform ---
TYPEFORM_ACCESS_TOKEN = os.environ.get("TYPEFORM_ACCESS_TOKEN", "")

# --- Beehiiv ---
BEEHIIV_API_KEY = os.environ.get("BEEHIIV_API_KEY", "")
BEEHIIV_PUBLICATION_ID = os.environ.get("BEEHIIV_PUBLICATION_ID", "")

# --- ConvertKit ---
CONVERTKIT_API_KEY = os.environ.get("CONVERTKIT_API_KEY", "")
CONVERTKIT_API_SECRET = os.environ.get("CONVERTKIT_API_SECRET", "")

# --- Linear ---
LINEAR_API_KEY = os.environ.get("LINEAR_API_KEY", "")

# --- Resend ---
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")

# --- Supabase ---
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# --- Notion AI ---
NOTION_AI_API_KEY = os.environ.get("NOTION_AI_API_KEY", "")

# --- Brave Search ---
BRAVE_SEARCH_API_KEY = os.environ.get("BRAVE_SEARCH_API_KEY", "")

# --- Wikipedia (optional) ---
WIKIPEDIA_ACCESS_TOKEN = os.environ.get("WIKIPEDIA_ACCESS_TOKEN", "")
WIKIPEDIA_USER_AGENT = os.environ.get("WIKIPEDIA_USER_AGENT", "")

# --- OpenWeatherMap ---
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")

# --- News API ---
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")

# --- Google Maps ---
GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

# --- Yelp ---
YELP_API_KEY = os.environ.get("YELP_API_KEY", "")

# --- OpenSea ---
OPENSEA_API_KEY = os.environ.get("OPENSEA_API_KEY", "")

# --- Binance ---
BINANCE_API_KEY = os.environ.get("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.environ.get("BINANCE_API_SECRET", "")
BINANCE_BASE_URL = os.environ.get("BINANCE_BASE_URL", "")

# --- Vercel ---
VERCEL_ACCESS_TOKEN = os.environ.get("VERCEL_ACCESS_TOKEN", "")
VERCEL_TEAM_ID = os.environ.get("VERCEL_TEAM_ID", "")

# --- Sentry ---
SENTRY_AUTH_TOKEN = os.environ.get("SENTRY_AUTH_TOKEN", "")
SENTRY_ORG = os.environ.get("SENTRY_ORG", "")
SENTRY_BASE_URL = os.environ.get("SENTRY_BASE_URL", "")

# --- Datadog ---
DATADOG_API_KEY = os.environ.get("DATADOG_API_KEY", "")
DATADOG_APP_KEY = os.environ.get("DATADOG_APP_KEY", "")
DATADOG_SITE = os.environ.get("DATADOG_SITE", "")

# --- PagerDuty ---
PAGERDUTY_API_KEY = os.environ.get("PAGERDUTY_API_KEY", "")
PAGERDUTY_FROM_EMAIL = os.environ.get("PAGERDUTY_FROM_EMAIL", "")

# --- Mixpanel ---
MIXPANEL_PROJECT_TOKEN = os.environ.get("MIXPANEL_PROJECT_TOKEN", "")
MIXPANEL_PROJECT_ID = os.environ.get("MIXPANEL_PROJECT_ID", "")
MIXPANEL_SERVICE_ACCOUNT_USER = os.environ.get("MIXPANEL_SERVICE_ACCOUNT_USER", "")
MIXPANEL_SERVICE_ACCOUNT_SECRET = os.environ.get("MIXPANEL_SERVICE_ACCOUNT_SECRET", "")

# --- Segment ---
SEGMENT_WRITE_KEY = os.environ.get("SEGMENT_WRITE_KEY", "")
SEGMENT_API_TOKEN = os.environ.get("SEGMENT_API_TOKEN", "")

# --- Algolia ---
ALGOLIA_APP_ID = os.environ.get("ALGOLIA_APP_ID", "")
ALGOLIA_API_KEY = os.environ.get("ALGOLIA_API_KEY", "")

# --- Contentful ---
CONTENTFUL_SPACE_ID = os.environ.get("CONTENTFUL_SPACE_ID", "")
CONTENTFUL_ACCESS_TOKEN = os.environ.get("CONTENTFUL_ACCESS_TOKEN", "")
CONTENTFUL_MANAGEMENT_TOKEN = os.environ.get("CONTENTFUL_MANAGEMENT_TOKEN", "")

# --- Plaid ---
PLAID_CLIENT_ID = os.environ.get("PLAID_CLIENT_ID", "")
PLAID_SECRET = os.environ.get("PLAID_SECRET", "")
PLAID_ENV = os.environ.get("PLAID_ENV", "sandbox")

# --- ClickUp ---
CLICKUP_API_TOKEN = os.environ.get("CLICKUP_API_TOKEN", "")

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
    "asana": "goliath.integrations.asana",
    "monday": "goliath.integrations.monday",
    "zendesk": "goliath.integrations.zendesk",
    "intercom": "goliath.integrations.intercom",
    "twitch": "goliath.integrations.twitch",
    "snapchat": "goliath.integrations.snapchat",
    "medium": "goliath.integrations.medium",
    "substack": "goliath.integrations.substack",
    "cloudflare": "goliath.integrations.cloudflare",
    "firebase": "goliath.integrations.firebase",
    "figma": "goliath.integrations.figma",
    "canva": "goliath.integrations.canva",
    "loom": "goliath.integrations.loom",
    "typeform": "goliath.integrations.typeform",
    "beehiiv": "goliath.integrations.beehiiv",
    "convertkit": "goliath.integrations.convertkit",
    "linear": "goliath.integrations.linear",
    "resend": "goliath.integrations.resend",
    "supabase": "goliath.integrations.supabase",
    "notion_ai": "goliath.integrations.notion_ai",
    "perplexity_search": "goliath.integrations.perplexity_search",
    "brave_search": "goliath.integrations.brave_search",
    "wikipedia": "goliath.integrations.wikipedia",
    "weather": "goliath.integrations.weather",
    "news": "goliath.integrations.news",
    "google_maps": "goliath.integrations.google_maps",
    "yelp": "goliath.integrations.yelp",
    "opensea": "goliath.integrations.opensea",
    "binance": "goliath.integrations.binance",
    "vercel": "goliath.integrations.vercel",
    "sentry": "goliath.integrations.sentry",
    "datadog": "goliath.integrations.datadog",
    "pagerduty": "goliath.integrations.pagerduty",
    "mixpanel": "goliath.integrations.mixpanel",
    "segment": "goliath.integrations.segment",
    "algolia": "goliath.integrations.algolia",
    "contentful": "goliath.integrations.contentful",
    "plaid": "goliath.integrations.plaid",
    "clickup": "goliath.integrations.clickup",
}

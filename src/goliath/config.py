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
}

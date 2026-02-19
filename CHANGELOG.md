# Changelog

All notable changes to GOLIATH are documented in this file.

## [0.1.0] - 2025-06-01

### Added

- **Core engine** — task execution engine with plugin-based model providers
- **4 AI providers** — xAI Grok (default), OpenAI, Anthropic Claude, Google Gemini
- **21 integrations:**
  - **Social & messaging:** X/Twitter, Instagram, Discord, Telegram, Slack, WhatsApp, Reddit
  - **Google ecosystem:** Gmail, Sheets, Drive, Calendar, Docs
  - **Developer tools:** GitHub, Web Scraper, Image Generation (DALL-E)
  - **Business & commerce:** YouTube, LinkedIn, Shopify, Stripe, Twilio SMS
  - **Productivity:** Notion
- **Persistent memory system** — conversation history and key-value fact store across sessions
- **Content moderation layer** — regex-based screening for 7 categories of harmful content (illegal activity, violence, hate speech, harassment, self-harm, sexual exploitation, spam/fraud)
- **Interactive CLI** — REPL with memory commands (`/remember`, `/recall`, `/forget`, `/facts`, `/history`)
- **Single-shot mode** — pass tasks directly via command line

### Security

- API tokens sent via `Authorization` headers (never in URLs or request bodies)
- URL scheme validation in web scraper (blocks `file://` and SSRF)
- Input length limits in CLI (32K characters) and memory commands
- Error messages sanitized to prevent credential leaks
- `SECURITY.md` vulnerability reporting policy
- `CODE_OF_CONDUCT.md` with responsible use guidelines

### Testing

- 265 tests across 5 test files
- Content moderation tests (142 cases across all 7 categories + safe inputs)
- Integration tests for all 21 integrations using `unittest.mock`

### CI/CD

- GitHub Actions workflow — lint (ruff) + test (Python 3.10–3.13)
- CI badge in README

### Packaging

- Published as `goliath-ai` on PyPI
- `pip install goliath-ai` with `goliath` CLI entrypoint

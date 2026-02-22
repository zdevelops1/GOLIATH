# Changelog

All notable changes to GOLIATH are documented in this file.

## [0.7.0] - 2026-02-21

### Added

- **10 new integrations** (batch 5), bringing the total from 67 to 77:
  - **Vercel** — deployments, projects, domains, environment variables
  - **Sentry** — error tracking, issues, events, project management
  - **Datadog** — metrics, monitors, events, alerting
  - **PagerDuty** — incidents, services, on-call schedules, escalation policies
  - **Mixpanel** — event tracking, user profiles, analytics queries
  - **Segment** — identify, track, page, group, batch analytics
  - **Algolia** — full-text search, index management, multi-search
  - **Contentful** — content entries, assets, content types, CMA publishing
  - **Plaid** — bank accounts, transactions, balances, identity, institutions
  - **ClickUp** — tasks, lists, spaces, folders, comments

- **66 new tests** for all batch 5 integrations:
  - Vercel (credential validation, auth headers, projects, deployments, domains, team params)
  - Sentry (credential + org validation, auth header, projects, issues, update issue)
  - Datadog (credential validation, DD headers, submit metric, monitors, events, custom site)
  - PagerDuty (credential validation, Token auth header, incidents, create incident, services, oncalls)
  - Mixpanel (credential validation, track event, token in payload, set user, SA auth required, batch)
  - Segment (credential validation, Basic auth header, identify, track, page, group, batch)
  - Algolia (credential validation, X-Algolia headers, search, save objects, get object, indices, app ID in URL)
  - Contentful (space ID + token validation, auth header, list entries, content types, CMA required, assets)
  - Plaid (credential validation, sandbox URL, link token, exchange token, balance, transactions, auth payload)
  - ClickUp (credential validation, auth header, teams, tasks, create task, comments, spaces)

### Changed

- Total integrations: 67 → 77
- Total tests: 464 → 530
- README updated with new integrations table, examples, and configuration reference
- Package version bumped to 0.7.0

---

## [0.6.1] - 2026-02-20

### Added

- **58 new tests for batch 4 integrations** covering all 10 integrations added in v0.6.0:
  - Notion AI (credential validation, fallback key, generate, summarize, 404 fallback)
  - Perplexity Search (auth, search with citations, quick search, recency filter)
  - Brave Search (auth header, web/news/image search endpoints)
  - Wikipedia (no-auth init, search, summary, random, on-this-day)
  - Weather / OpenWeatherMap (credential validation, current/coords/forecast/geocode/air quality)
  - News API (credential validation, top headlines, search, sources)
  - Google Maps (credential validation, geocode, reverse geocode, nearby search, directions, distance matrix, autocomplete)
  - Yelp (credential validation, auth header, search, business details, reviews, phone search)
  - OpenSea (credential validation, auth header, collections, NFTs, stats, events)
  - Binance (no-key init for public endpoints, API key header, price, order book, klines, signed request validation, 24h stats)

### Changed

- Total tests: 406 → 464
- README updated with test count
- Package version bumped to 0.6.1

---

## [0.6.0] - 2026-02-19

### Added

- **10 new integrations (57 → 67 total):**
  - **AI & search:** Notion AI (text generation, summarization, translation, grammar), Perplexity Search (AI-powered web search with citations), Brave Search (web, news, image search, summarization)
  - **Knowledge:** Wikipedia (articles, summaries, search, on-this-day — no API key required)
  - **Data & weather:** Weather API / OpenWeatherMap (current weather, forecasts, air quality, geocoding), News API (headlines, article search, sources)
  - **Location:** Google Maps (geocoding, places, directions, distance matrix), Yelp (business search, reviews, categories)
  - **Web3 & crypto:** OpenSea (NFT collections, assets, events, offers), Binance (market data, order books, klines, account info)

### Changed

- Total integrations: 57 → 67
- README updated with all 67 integrations
- Package version bumped to 0.6.0

---

## [0.5.0] - 2026-02-19

### Added

- **9 new integrations (48 → 57 total):**
  - **Design:** Figma (files, components, comments, image exports), Canva (designs, folders, exports, brand templates)
  - **Video:** Loom (videos, transcripts, folders, oEmbed)
  - **Forms:** Typeform (forms, responses, workspaces, insights)
  - **Newsletters:** Beehiiv (posts, subscribers, publication stats), ConvertKit (subscribers, forms, sequences, broadcasts)
  - **Project management:** Linear (issues, projects, teams, comments via GraphQL)
  - **Email:** Resend (transactional email, domains, batch sending)
  - **Backend-as-a-Service:** Supabase (PostgREST database CRUD, storage, auth)

### Changed

- Total integrations: 48 → 57
- README updated with all 57 integrations
- Package version bumped to 0.5.0

---

## [0.4.0] - 2026-02-19

### Added

- **10 new integrations (38 → 48 total):**
  - **Project management:** Asana (projects, tasks, workspaces, comments), Monday.com (boards, items, updates via GraphQL)
  - **Customer support:** Zendesk (tickets, users, organizations, search), Intercom (contacts, conversations, messaging)
  - **Streaming & social:** Twitch (channels, streams, chat, clips), Snapchat (campaigns, ad squads, creative media)
  - **Publishing:** Medium (posts, publications), Substack (drafts, newsletter publishing, subscriber stats)
  - **Infrastructure:** Cloudflare (DNS, zones, Workers, caching), Firebase (Firestore, Realtime Database, Auth)

### Changed

- Total integrations: 38 → 48
- README updated with all 48 integrations
- Package version bumped to 0.4.0

---

## [0.3.0] - 2026-02-19

### Added

- **5 new model providers (4 → 9 total):**
  - **Mistral AI** — Mistral Large, Medium, Small, Codestral (`mistralai` SDK)
  - **DeepSeek** — DeepSeek Chat and Reasoner (OpenAI-compatible endpoint)
  - **Ollama** — Local models: Llama 3.1, Mistral, Phi, CodeLlama, etc. (no API key needed)
  - **Cohere** — Command R+, Command R, Command Light (`cohere` SDK)
  - **Perplexity** — Sonar and Sonar Pro search-augmented models (OpenAI-compatible endpoint)
- **7 new integrations (31 → 38 total):**
  - **Cloud storage:** Dropbox (files, folders, sharing), Amazon S3 (objects, buckets, presigned URLs)
  - **Project management:** Jira (issues, transitions, comments, JQL search), Trello (boards, lists, cards, checklists)
  - **Databases & tables:** Airtable (bases, tables, records, formulas)
  - **Email marketing:** Mailchimp (audiences, subscribers, campaigns), SendGrid (transactional email, templates, contacts)

### Changed

- Dependencies: added `mistralai>=1.0.0`, `cohere>=5.0.0`, `boto3>=1.26.0`
- Total model providers: 4 → 9
- Total integrations: 31 → 38
- README updated with all 9 providers and 38 integrations
- Package version bumped to 0.3.0

---

## [0.2.0] - 2026-02-19

### Added

- **10 new integrations (21 → 31 total):**
  - **Social & content:** Pinterest, TikTok, Spotify
  - **Meetings & scheduling:** Zoom, Calendly
  - **CRM & sales:** HubSpot, Salesforce
  - **CMS & web:** WordPress, Webflow
  - **Payments:** PayPal (sandbox + live)
- **73 new tests** for all 10 integrations covering credential validation, auth patterns (Bearer token, HTTP Basic, OAuth client credentials, Server-to-Server OAuth, password flow), API call construction, and sandbox/live toggling

### Changed

- Total test count: 265 → 338
- README updated with 31 integrations, expanded architecture tree, and config reference

---

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

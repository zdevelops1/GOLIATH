# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in GOLIATH, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

Instead, please email **security@goliath-ai.dev** with:

1. A description of the vulnerability
2. Steps to reproduce the issue
3. The potential impact
4. Any suggested fixes (optional)

You should receive an acknowledgment within 48 hours. We will work with you to understand the issue and coordinate a fix before any public disclosure.

## Security Practices

### Credential Management

- All API keys and secrets are loaded exclusively from environment variables or a `.env` file.
- The `.env` file is listed in `.gitignore` and must never be committed to version control.
- No credentials are hardcoded anywhere in the source code.
- If you suspect a credential has been exposed, rotate it immediately.

### Content Moderation

GOLIATH includes a built-in content moderation layer (`core/moderation.py`) that screens all tasks before they reach the AI model. The following categories are blocked:

- Illegal activity (drugs, weapons, hacking)
- Violence and threats
- Hate speech
- Harassment, stalking, and doxxing
- Self-harm and suicide content
- Sexual exploitation of minors
- Spam, phishing, and fraud

### Input Validation

- CLI input is capped at 32,000 characters to prevent resource exhaustion.
- Memory keys and values have length limits (128 and 4,096 characters respectively).
- URL scheme validation prevents SSRF and local file access in the web scraper.
- API tokens are sent via `Authorization` headers, not URL query parameters or request bodies.

### Dependencies

- All dependencies are pinned with minimum versions in `requirements.txt` and `pyproject.toml`.
- We recommend running `pip audit` regularly to check for known vulnerabilities in dependencies.

## Acknowledgments

We appreciate the security research community and will credit reporters (with permission) in release notes.

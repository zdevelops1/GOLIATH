"""
Perplexity model provider — connects to the Perplexity API.

Uses the OpenAI-compatible chat completions endpoint that Perplexity exposes,
so the only dependency is the `openai` package (already installed).

Perplexity models are search-augmented — they can access real-time web data
to ground their responses in current information.

SETUP INSTRUCTIONS
==================

1. Create an account at https://www.perplexity.ai/

2. Go to https://www.perplexity.ai/settings/api and generate an API key.

3. Add to your .env:
     PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxx

4. (Optional) Override the default model:
     PERPLEXITY_DEFAULT_MODEL=sonar-pro

Available models:
  - sonar              (lightweight, fast search-augmented model)
  - sonar-pro          (advanced search-augmented model, higher quality)
  - sonar-reasoning    (reasoning with search augmentation)

IMPORTANT NOTES
===============
- Perplexity responses often include citations in the response text.
- Pricing: https://docs.perplexity.ai/guides/pricing
- Rate limits depend on your subscription tier.
- The API is OpenAI-compatible (same SDK, same message format).
"""

from openai import OpenAI

from goliath import config
from goliath.models.base import BaseProvider, ModelResponse


class PerplexityProvider(BaseProvider):
    """Perplexity provider (search-augmented AI) using the OpenAI-compatible API."""

    name = "perplexity"

    def __init__(self):
        if not config.PERPLEXITY_API_KEY:
            raise RuntimeError(
                "PERPLEXITY_API_KEY is not set. "
                "Get one at https://www.perplexity.ai/settings/api "
                "and add it to .env or export as an environment variable."
            )
        self.client = OpenAI(
            api_key=config.PERPLEXITY_API_KEY,
            base_url=config.PERPLEXITY_BASE_URL,
        )
        self.model = config.PERPLEXITY_DEFAULT_MODEL

    def run(
        self, prompt: str, system_prompt: str = "", history: list[dict] | None = None
    ) -> ModelResponse:
        """Send a task prompt to Perplexity and return the response."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=config.MAX_TOKENS,
            temperature=config.TEMPERATURE,
        )

        choice = completion.choices[0]
        usage = completion.usage

        return ModelResponse(
            content=choice.message.content,
            model=self.model,
            provider=self.name,
            usage={
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            },
        )

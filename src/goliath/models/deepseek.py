"""
DeepSeek model provider — connects to the DeepSeek API.

Uses the OpenAI-compatible chat completions endpoint that DeepSeek exposes,
so the only dependency is the `openai` package (already installed).

SETUP INSTRUCTIONS
==================

1. Create an account at https://platform.deepseek.com/

2. Go to https://platform.deepseek.com/api_keys and create an API key.

3. Add to your .env:
     DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx

4. (Optional) Override the default model:
     DEEPSEEK_DEFAULT_MODEL=deepseek-reasoner

Available models:
  - deepseek-chat      (general-purpose, fast, cost-effective)
  - deepseek-reasoner  (chain-of-thought reasoning, slower but more accurate)

IMPORTANT NOTES
===============
- Pricing: https://platform.deepseek.com/api-docs/pricing
- Rate limits depend on your account tier.
- The API is fully OpenAI-compatible (same SDK, same message format).
"""

from openai import OpenAI

from goliath import config
from goliath.models.base import BaseProvider, ModelResponse


class DeepSeekProvider(BaseProvider):
    """DeepSeek provider using the OpenAI-compatible API."""

    name = "deepseek"

    def __init__(self):
        if not config.DEEPSEEK_API_KEY:
            raise RuntimeError(
                "DEEPSEEK_API_KEY is not set. "
                "Get one at https://platform.deepseek.com/api_keys "
                "and add it to .env or export as an environment variable."
            )
        self.client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
        )
        self.model = config.DEEPSEEK_DEFAULT_MODEL

    def run(
        self, prompt: str, system_prompt: str = "", history: list[dict] | None = None
    ) -> ModelResponse:
        """Send a task prompt to DeepSeek and return the response."""
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

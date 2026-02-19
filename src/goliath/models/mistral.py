"""
Mistral model provider — connects to the Mistral AI API.

Uses the official `mistralai` package for full access to Mistral models
including Mistral Large, Medium, Small, and Codestral.

SETUP INSTRUCTIONS
==================

1. Create an account at https://console.mistral.ai/

2. Go to https://console.mistral.ai/api-keys/ and create an API key.

3. Add to your .env:
     MISTRAL_API_KEY=xxxxxxxxxxxxxxxx

4. (Optional) Override the default model:
     MISTRAL_DEFAULT_MODEL=mistral-large-latest

Available models:
  - mistral-large-latest   (flagship model, best quality)
  - mistral-medium-latest  (balanced performance/cost)
  - mistral-small-latest   (fast, cost-effective)
  - codestral-latest       (optimised for code generation)
  - open-mistral-nemo      (open-weight, strong reasoning)

IMPORTANT NOTES
===============
- Pricing: https://mistral.ai/technology/#pricing
- Rate limits depend on your subscription tier.
- Install the SDK: pip install mistralai>=1.0.0
"""

from mistralai import Mistral

from goliath import config
from goliath.models.base import BaseProvider, ModelResponse


class MistralProvider(BaseProvider):
    """Mistral AI provider (Large, Medium, Small, Codestral, etc.)."""

    name = "mistral"

    def __init__(self):
        if not config.MISTRAL_API_KEY:
            raise RuntimeError(
                "MISTRAL_API_KEY is not set. "
                "Get one at https://console.mistral.ai/api-keys/ "
                "and add it to .env or export as an environment variable."
            )
        self.client = Mistral(api_key=config.MISTRAL_API_KEY)
        self.model = config.MISTRAL_DEFAULT_MODEL

    def run(
        self, prompt: str, system_prompt: str = "", history: list[dict] | None = None
    ) -> ModelResponse:
        """Send a task prompt to Mistral and return the response."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.complete(
            model=self.model,
            messages=messages,
            max_tokens=config.MAX_TOKENS,
            temperature=config.TEMPERATURE,
        )

        choice = response.choices[0]
        usage = response.usage

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

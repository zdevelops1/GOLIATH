"""
Cohere model provider — connects to the Cohere API.

Uses the official `cohere` package for access to Command R, Command R+,
and other Cohere models.

SETUP INSTRUCTIONS
==================

1. Create an account at https://dashboard.cohere.com/

2. Go to https://dashboard.cohere.com/api-keys and create an API key.

3. Add to your .env:
     COHERE_API_KEY=xxxxxxxxxxxxxxxx

4. (Optional) Override the default model:
     COHERE_DEFAULT_MODEL=command-r-plus

Available models:
  - command-r-plus    (flagship model, best for complex tasks)
  - command-r         (balanced performance, good for most tasks)
  - command-light     (fast, cost-effective)

IMPORTANT NOTES
===============
- Pricing: https://cohere.com/pricing
- Rate limits: 10K requests/minute on production keys.
- Cohere uses "CHATBOT" and "USER" roles internally; this provider
  maps standard "assistant"/"user" roles automatically.
- Install the SDK: pip install cohere>=5.0.0
"""

import cohere

from goliath import config
from goliath.models.base import BaseProvider, ModelResponse


class CohereProvider(BaseProvider):
    """Cohere provider (Command R+, Command R, etc.)."""

    name = "cohere"

    def __init__(self):
        if not config.COHERE_API_KEY:
            raise RuntimeError(
                "COHERE_API_KEY is not set. "
                "Get one at https://dashboard.cohere.com/api-keys "
                "and add it to .env or export as an environment variable."
            )
        self.client = cohere.ClientV2(api_key=config.COHERE_API_KEY)
        self.model = config.COHERE_DEFAULT_MODEL

    def run(
        self, prompt: str, system_prompt: str = "", history: list[dict] | None = None
    ) -> ModelResponse:
        """Send a task prompt to Cohere and return the response."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat(
            model=self.model,
            messages=messages,
            max_tokens=config.MAX_TOKENS,
            temperature=config.TEMPERATURE,
        )

        usage = response.usage
        prompt_tokens = usage.tokens.input_tokens if usage and usage.tokens else 0
        completion_tokens = usage.tokens.output_tokens if usage and usage.tokens else 0

        return ModelResponse(
            content=response.message.content[0].text,
            model=self.model,
            provider=self.name,
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
        )

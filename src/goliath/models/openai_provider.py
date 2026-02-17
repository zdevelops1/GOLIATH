"""
OpenAI model provider — connects to the OpenAI API.

Uses the official openai package (already installed for Grok).
Supports GPT-4o, GPT-4, GPT-3.5-turbo, and any future OpenAI model.
"""

from openai import OpenAI

from goliath import config
from goliath.models.base import BaseProvider, ModelResponse


class OpenAIProvider(BaseProvider):
    """OpenAI provider (GPT-4o, GPT-4, etc.)."""

    name = "openai"

    def __init__(self):
        if not config.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is not set. "
                "Export it as an environment variable or add it to .env."
            )
        self.client = OpenAI(api_key=config.OPENAI_API_KEY)
        self.model = config.OPENAI_DEFAULT_MODEL

    def run(self, prompt: str, system_prompt: str = "") -> ModelResponse:
        """Send a task prompt to OpenAI and return the response."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
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

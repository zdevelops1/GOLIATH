"""
Grok model provider — connects to the xAI API.

Uses the OpenAI-compatible chat completions endpoint that xAI exposes,
so the only dependency is the `openai` package.
"""

from openai import OpenAI

from goliath import config
from goliath.models.base import BaseProvider, ModelResponse


class GrokProvider(BaseProvider):
    """xAI Grok provider using the OpenAI-compatible API."""

    name = "grok"

    def __init__(self):
        if not config.XAI_API_KEY:
            raise RuntimeError(
                "XAI_API_KEY is not set. "
                "Export it as an environment variable or set it in config.py."
            )
        self.client = OpenAI(
            api_key=config.XAI_API_KEY,
            base_url=config.XAI_BASE_URL,
        )
        self.model = config.XAI_DEFAULT_MODEL

    def run(
        self, prompt: str, system_prompt: str = "", history: list[dict] | None = None
    ) -> ModelResponse:
        """Send a task prompt to Grok and return the response."""
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

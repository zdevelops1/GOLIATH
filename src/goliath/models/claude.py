"""
Claude model provider — connects to the Anthropic API.

Uses the official anthropic package. Supports Claude Opus, Sonnet,
Haiku, and any future Anthropic model.
"""

import anthropic

from goliath import config
from goliath.models.base import BaseProvider, ModelResponse


class ClaudeProvider(BaseProvider):
    """Anthropic Claude provider (Opus, Sonnet, Haiku, etc.)."""

    name = "claude"

    def __init__(self):
        if not config.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. "
                "Export it as an environment variable or add it to .env."
            )
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.model = config.ANTHROPIC_DEFAULT_MODEL

    def run(self, prompt: str, system_prompt: str = "") -> ModelResponse:
        """Send a task prompt to Claude and return the response."""
        kwargs = {
            "model": self.model,
            "max_tokens": config.MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)

        # Claude returns a list of content blocks; extract the text.
        content = "".join(
            block.text for block in response.content if block.type == "text"
        )

        return ModelResponse(
            content=content,
            model=self.model,
            provider=self.name,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
        )

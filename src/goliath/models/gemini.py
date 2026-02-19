"""
Gemini model provider — connects to the Google Generative AI API.

Uses the official google-genai package. Supports Gemini 2.0 Flash,
Gemini 1.5 Pro, and any future Google model.
"""

from google import genai
from google.genai import types

from goliath import config
from goliath.models.base import BaseProvider, ModelResponse


class GeminiProvider(BaseProvider):
    """Google Gemini provider (2.0 Flash, 1.5 Pro, etc.)."""

    name = "gemini"

    def __init__(self):
        if not config.GOOGLE_API_KEY:
            raise RuntimeError(
                "GOOGLE_API_KEY is not set. "
                "Export it as an environment variable or add it to .env."
            )
        self.client = genai.Client(api_key=config.GOOGLE_API_KEY)
        self.model = config.GOOGLE_DEFAULT_MODEL

    def run(
        self, prompt: str, system_prompt: str = "", history: list[dict] | None = None
    ) -> ModelResponse:
        """Send a task prompt to Gemini and return the response."""
        config_kwargs = {
            "max_output_tokens": config.MAX_TOKENS,
            "temperature": config.TEMPERATURE,
        }
        if system_prompt:
            config_kwargs["system_instruction"] = system_prompt

        # Build contents: history turns + current prompt
        contents = []
        if history:
            for turn in history:
                role = "model" if turn["role"] == "assistant" else turn["role"]
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part(text=turn["content"])],
                    )
                )
        contents.append(prompt)

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(**config_kwargs),
        )

        usage = response.usage_metadata

        return ModelResponse(
            content=response.text,
            model=self.model,
            provider=self.name,
            usage={
                "prompt_tokens": usage.prompt_token_count or 0,
                "completion_tokens": usage.candidates_token_count or 0,
                "total_tokens": usage.total_token_count or 0,
            },
        )

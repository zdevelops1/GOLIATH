"""
Ollama model provider — connects to a local Ollama instance.

Uses the OpenAI-compatible chat completions endpoint that Ollama exposes,
so the only dependency is the `openai` package (already installed).
No API key needed — Ollama runs entirely on your machine.

SETUP INSTRUCTIONS
==================

1. Install Ollama from https://ollama.com/download

2. Pull a model:
     ollama pull llama3.1
     ollama pull mistral
     ollama pull phi3
     ollama pull codellama

3. Start the Ollama server (runs automatically after install):
     ollama serve

4. (Optional) Configure in your .env:
     OLLAMA_BASE_URL=http://localhost:11434/v1   # default
     OLLAMA_DEFAULT_MODEL=llama3.1               # default

Available models (run `ollama list` to see installed):
  - llama3.1         (Meta Llama 3.1 — general purpose, 8B/70B/405B)
  - mistral          (Mistral 7B — fast, efficient)
  - phi3             (Microsoft Phi-3 — small but capable)
  - codellama        (Meta Code Llama — code generation)
  - gemma2           (Google Gemma 2 — lightweight)
  - qwen2.5          (Alibaba Qwen 2.5 — multilingual)

IMPORTANT NOTES
===============
- No API key required — fully local and private.
- Performance depends on your hardware (GPU recommended for larger models).
- Default port is 11434. Change OLLAMA_BASE_URL if you use a different port.
- Ollama must be running before using this provider.
"""

from openai import OpenAI

from goliath import config
from goliath.models.base import BaseProvider, ModelResponse


class OllamaProvider(BaseProvider):
    """Ollama provider for local models (Llama, Mistral, Phi, etc.)."""

    name = "ollama"

    def __init__(self):
        self.client = OpenAI(
            api_key="ollama",  # Ollama ignores this but the SDK requires it
            base_url=config.OLLAMA_BASE_URL,
        )
        self.model = config.OLLAMA_DEFAULT_MODEL

    def run(
        self, prompt: str, system_prompt: str = "", history: list[dict] | None = None
    ) -> ModelResponse:
        """Send a task prompt to a local Ollama model and return the response."""
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
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
            },
        )

"""
Base model provider interface.

Every model provider (Grok, OpenAI, Anthropic, local LLMs, etc.) must
subclass BaseProvider and implement `run`. This keeps the engine
model-agnostic — swap providers without touching any other code.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ModelResponse:
    """Standardised response returned by every provider."""
    content: str
    model: str
    provider: str
    usage: dict  # {"prompt_tokens": int, "completion_tokens": int, "total_tokens": int}


class BaseProvider(ABC):
    """Abstract base class for all model providers."""

    name: str = "base"

    @abstractmethod
    def run(
        self,
        prompt: str,
        system_prompt: str = "",
        history: list[dict] | None = None,
    ) -> ModelResponse:
        """Send a prompt to the model and return a ModelResponse.

        Args:
            prompt:        The current user message.
            system_prompt: System instructions.
            history:       Prior conversation turns [{"role": ..., "content": ...}].
        """
        ...

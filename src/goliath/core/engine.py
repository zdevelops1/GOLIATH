"""
GOLIATH Task Execution Engine

The engine is the heart of GOLIATH. It:
  1. Accepts a plain-English task from any interface (CLI, API, etc.)
  2. Resolves the correct model provider
  3. Sends the task to the model
  4. Returns the structured result

The engine is intentionally thin — it orchestrates, it doesn't do the
work itself. That keeps it easy to extend with middleware, hooks, or
multi-step pipelines later.
"""

import importlib

from goliath import config
from goliath.core.moderation import check as moderate
from goliath.memory.store import Memory
from goliath.models.base import BaseProvider, ModelResponse


class Engine:
    """Core task execution engine."""

    def __init__(self, provider_name: str | None = None):
        self.provider = self._load_provider(provider_name or config.DEFAULT_PROVIDER)
        self.memory = Memory()

    def execute(self, task: str) -> ModelResponse:
        """Execute a plain-English task and return the model response."""
        # Content moderation — block harmful requests before they reach the model
        moderate(task)

        # Build system prompt with any stored facts
        system_prompt = config.SYSTEM_PROMPT
        facts_context = self.memory.facts_as_context()
        if facts_context:
            system_prompt = f"{system_prompt}\n\n{facts_context}"

        # Get conversation history for context
        history = self.memory.get_history()

        result = self.provider.run(
            prompt=task,
            system_prompt=system_prompt,
            history=history or None,
        )

        # Save this turn to memory
        self.memory.add_turn("user", task)
        self.memory.add_turn("assistant", result.content)

        return result

    # -- internal helpers --------------------------------------------------

    @staticmethod
    def _load_provider(name: str) -> BaseProvider:
        """Dynamically load a model provider by its registered name."""
        if name not in config.MODEL_PROVIDERS:
            available = ", ".join(config.MODEL_PROVIDERS) or "(none)"
            raise ValueError(f"Unknown provider '{name}'. Available: {available}")

        module_path = config.MODEL_PROVIDERS[name]
        module = importlib.import_module(module_path)

        # Convention: provider class is the only BaseProvider subclass in the module.
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BaseProvider)
                and attr is not BaseProvider
            ):
                return attr()

        raise ImportError(f"No BaseProvider subclass found in '{module_path}'")

"""
GOLIATH Memory Store

Persistent memory system with two layers:
  - Conversation history: recent task/response pairs fed as context to the model
  - Facts: key-value store for things GOLIATH should always remember

Data is stored as JSON on disk so it survives across sessions.
The memory file location is configurable via MEMORY_PATH in config.

Usage:
    from goliath.memory.store import Memory

    mem = Memory()

    # Conversation history (auto-managed by the engine)
    mem.add_turn("user", "What is Python?")
    mem.add_turn("assistant", "Python is a programming language.")
    history = mem.get_history()

    # Facts (persistent key-value pairs)
    mem.remember("name", "GOLIATH")
    mem.remember("owner", "zdevelops1")
    print(mem.recall("name"))        # "GOLIATH"
    print(mem.facts())               # {"name": "GOLIATH", "owner": "zdevelops1"}
    mem.forget("owner")

    # Reset
    mem.clear_history()              # clear conversation only
    mem.clear_all()                  # clear everything
"""

import json
from pathlib import Path

from goliath import config


class Memory:
    """Persistent memory with conversation history and fact storage."""

    def __init__(self, path: str | None = None):
        self.path = Path(path or config.MEMORY_PATH)
        self._data = self._load()

    # -- Conversation history ----------------------------------------------

    def add_turn(self, role: str, content: str) -> None:
        """Add a conversation turn (role: 'user' or 'assistant')."""
        self._data["history"].append({"role": role, "content": content})

        # Trim to max history length
        max_turns = config.MEMORY_MAX_HISTORY
        if len(self._data["history"]) > max_turns:
            self._data["history"] = self._data["history"][-max_turns:]

        self._save()

    def get_history(self) -> list[dict]:
        """Return conversation history as a list of {"role": ..., "content": ...}."""
        return list(self._data["history"])

    def clear_history(self) -> None:
        """Clear conversation history but keep facts."""
        self._data["history"] = []
        self._save()

    # -- Facts (key-value) -------------------------------------------------

    def remember(self, key: str, value: str) -> None:
        """Store a persistent fact."""
        self._data["facts"][key] = value
        self._save()

    def recall(self, key: str) -> str | None:
        """Retrieve a fact by key. Returns None if not found."""
        return self._data["facts"].get(key)

    def facts(self) -> dict[str, str]:
        """Return all stored facts."""
        return dict(self._data["facts"])

    def forget(self, key: str) -> None:
        """Remove a fact by key."""
        self._data["facts"].pop(key, None)
        self._save()

    # -- Utilities ---------------------------------------------------------

    def clear_all(self) -> None:
        """Clear all memory (history and facts)."""
        self._data = {"history": [], "facts": {}}
        self._save()

    def summary(self) -> str:
        """Return a human-readable summary of memory state."""
        h = len(self._data["history"])
        f = len(self._data["facts"])
        return f"{h} conversation turns, {f} stored facts"

    def facts_as_context(self) -> str:
        """Format facts as a string to inject into the system prompt."""
        if not self._data["facts"]:
            return ""
        lines = [f"- {k}: {v}" for k, v in self._data["facts"].items()]
        return "Known facts:\n" + "\n".join(lines)

    # -- internal helpers --------------------------------------------------

    def _load(self) -> dict:
        """Load memory from disk or create empty state."""
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                # Ensure expected structure
                data.setdefault("history", [])
                data.setdefault("facts", {})
                return data
            except (json.JSONDecodeError, KeyError):
                pass
        return {"history": [], "facts": {}}

    def _save(self) -> None:
        """Persist memory to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self._data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

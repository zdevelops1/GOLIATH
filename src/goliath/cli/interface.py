"""
GOLIATH CLI Interface

Interactive REPL that lets you type tasks and see GOLIATH respond.
Supports single-shot mode (`goliath "do something"`) and interactive mode.

Memory commands (interactive mode):
  /memory          — show memory status
  /history         — show conversation history
  /remember k v    — store a persistent fact
  /recall k        — retrieve a stored fact
  /forget k        — remove a stored fact
  /facts           — list all stored facts
  /clear history   — clear conversation history
  /clear all       — clear all memory
"""

import sys

from goliath.core.engine import Engine
from goliath.core.moderation import ModerationError


BANNER = r"""
   ██████   ██████  ██      ██  █████  ████████ ██   ██
  ██       ██    ██ ██      ██ ██   ██    ██    ██   ██
  ██   ███ ██    ██ ██      ██ ███████    ██    ███████
  ██    ██ ██    ██ ██      ██ ██   ██    ██    ██   ██
   ██████   ██████  ███████ ██ ██   ██    ██    ██   ██

  Universal AI Automation Engine
  Type a task. Type 'quit' to exit.
  Type '/memory' for memory commands.
"""


def _handle_memory_command(engine: Engine, task: str) -> bool:
    """Handle /memory commands. Returns True if the input was a command."""
    parts = task.split(maxsplit=2)
    cmd = parts[0].lower()

    if cmd == "/memory":
        print(f"\n  Memory: {engine.memory.summary()}")
        print(f"  File:   {engine.memory.path}")
        return True

    if cmd == "/history":
        history = engine.memory.get_history()
        if not history:
            print("\n  No conversation history.")
        else:
            print()
            for turn in history:
                role = turn["role"].upper()
                text = turn["content"][:120] + ("..." if len(turn["content"]) > 120 else "")
                print(f"  [{role}] {text}")
        return True

    if cmd == "/remember":
        if len(parts) < 3:
            print("\n  Usage: /remember <key> <value>")
            return True
        key, value = parts[1], parts[2]
        if len(key) > 128:
            print("\n  [ERROR] Key too long (max 128 characters).")
            return True
        if len(value) > 4096:
            print("\n  [ERROR] Value too long (max 4,096 characters).")
            return True
        engine.memory.remember(key, value)
        print(f"\n  Remembered: {key} = {value}")
        return True

    if cmd == "/recall":
        if len(parts) < 2:
            print("\n  Usage: /recall <key>")
            return True
        value = engine.memory.recall(parts[1])
        if value is None:
            print(f"\n  No fact stored for '{parts[1]}'.")
        else:
            print(f"\n  {parts[1]} = {value}")
        return True

    if cmd == "/forget":
        if len(parts) < 2:
            print("\n  Usage: /forget <key>")
            return True
        engine.memory.forget(parts[1])
        print(f"\n  Forgot: {parts[1]}")
        return True

    if cmd == "/facts":
        facts = engine.memory.facts()
        if not facts:
            print("\n  No stored facts.")
        else:
            print()
            for k, v in facts.items():
                print(f"  {k}: {v}")
        return True

    if cmd == "/clear":
        target = parts[1].lower() if len(parts) > 1 else ""
        if target == "history":
            engine.memory.clear_history()
            print("\n  Conversation history cleared.")
        elif target == "all":
            engine.memory.clear_all()
            print("\n  All memory cleared.")
        else:
            print("\n  Usage: /clear history | /clear all")
        return True

    return False


def run_interactive():
    """Launch the interactive REPL."""
    print(BANNER)

    try:
        engine = Engine()
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    print(f"  Memory: {engine.memory.summary()}\n")

    while True:
        try:
            task = input("\nGOLIATH > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not task:
            continue
        if len(task) > 32000:
            print("\n[ERROR] Input too long (max 32,000 characters).")
            continue
        if task.lower() in ("quit", "exit"):
            print("Shutting down.")
            break

        # Check for memory commands
        if task.startswith("/"):
            if _handle_memory_command(engine, task):
                continue

        try:
            result = engine.execute(task)
            print(f"\n{result.content}")
            print(f"\n  [{result.provider}:{result.model} | {result.usage['total_tokens']} tokens]")
        except ModerationError as exc:
            print(f"\n[BLOCKED] {exc}")
        except Exception as exc:
            print(f"\n[ERROR] {exc}")


def run_once(task: str):
    """Execute a single task and print the result."""
    try:
        engine = Engine()
        result = engine.execute(task)
        print(result.content)
    except ModerationError as exc:
        print(f"[BLOCKED] {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

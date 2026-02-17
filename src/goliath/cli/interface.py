"""
GOLIATH CLI Interface

Interactive REPL that lets you type tasks and see GOLIATH respond.
Supports single-shot mode (`goliath "do something"`) and interactive mode.
"""

import sys

from goliath.core.engine import Engine


BANNER = r"""
   ██████   ██████  ██      ██  █████  ████████ ██   ██
  ██       ██    ██ ██      ██ ██   ██    ██    ██   ██
  ██   ███ ██    ██ ██      ██ ███████    ██    ███████
  ██    ██ ██    ██ ██      ██ ██   ██    ██    ██   ██
   ██████   ██████  ███████ ██ ██   ██    ██    ██   ██

  Universal AI Automation Engine
  Type a task. Type 'quit' to exit.
"""


def run_interactive():
    """Launch the interactive REPL."""
    print(BANNER)

    try:
        engine = Engine()
    except RuntimeError as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

    while True:
        try:
            task = input("\nGOLIATH > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            break

        if not task:
            continue
        if task.lower() in ("quit", "exit"):
            print("Shutting down.")
            break

        try:
            result = engine.execute(task)
            print(f"\n{result.content}")
            print(f"\n  [{result.provider}:{result.model} | {result.usage['total_tokens']} tokens]")
        except Exception as exc:
            print(f"\n[ERROR] {exc}")


def run_once(task: str):
    """Execute a single task and print the result."""
    try:
        engine = Engine()
        result = engine.execute(task)
        print(result.content)
    except Exception as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

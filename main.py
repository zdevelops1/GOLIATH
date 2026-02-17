#!/usr/bin/env python3
"""
GOLIATH — Universal AI Automation Engine

Usage:
    python main.py                  # interactive mode
    python main.py "summarise X"   # single-shot mode
"""

import sys

from cli.interface import run_interactive, run_once


def main():
    if len(sys.argv) > 1:
        # Single-shot: join all args as the task string
        task = " ".join(sys.argv[1:])
        run_once(task)
    else:
        run_interactive()


if __name__ == "__main__":
    main()

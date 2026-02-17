#!/usr/bin/env python3
"""
GOLIATH — Universal AI Automation Engine

Usage:
    python main.py                  # interactive mode
    python main.py "summarise X"   # single-shot mode
    goliath "summarise X"          # after pip install
"""

from goliath.main import main

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Small shared I/O helpers for hook-safe feature-map state files."""
import os


def append_gitignore(root, entry):
    gi_path = os.path.join(root, ".gitignore")
    try:
        existing = ""
        if os.path.isfile(gi_path):
            with open(gi_path, encoding="utf-8") as f:
                existing = f.read()
        if entry in existing:
            return
        with open(gi_path, "a", encoding="utf-8") as f:
            if existing and not existing.endswith("\n"):
                f.write("\n")
            f.write(f"{entry}\n")
    except Exception:
        pass

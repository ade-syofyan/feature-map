#!/usr/bin/env python3
"""Registry repo per mesin untuk flow multi-repo: nama repo -> path lokal.

Lokasi default ~/.claude/feature-maps/registry.json, override via env
FEATURE_MAP_REGISTRY. Semua fungsi aman dipanggil dari hook.
"""
import json
import os
import tempfile

REGISTRY_ENV = "FEATURE_MAP_REGISTRY"


def _registry_path():
    return os.environ.get(REGISTRY_ENV) or os.path.expanduser(
        "~/.claude/feature-maps/registry.json")


def load_registry():
    try:
        with open(_registry_path(), encoding="utf-8") as f:
            reg = json.load(f)
        if not isinstance(reg, dict) or not isinstance(reg.get("repos"), dict):
            return {"repos": {}}
        return reg
    except Exception:
        return {"repos": {}}


def save_registry(reg):
    try:
        path = _registry_path()
        d = os.path.dirname(path)
        os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(reg, f, indent=2)
        os.replace(tmp, path)
    except Exception:
        pass


def resolve(name):
    path = load_registry()["repos"].get(name)
    if path and os.path.isdir(path):
        return path
    return None


def default_repo_name(root):
    return os.path.basename(os.path.normpath(root)).lower().replace(" ", "-")

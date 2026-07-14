"""Shared config loader for the AI Operations Manager pipeline scripts.

Reads config/.env (same file/format ghl_api.py uses) merged with the real
process environment, which always wins. Import ENV and read keys from it,
or use get()/require() below.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(ROOT, "config", ".env")


def load_env(path):
    env = {}
    if not os.path.exists(path):
        return env
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


ENV = {**load_env(ENV_PATH), **os.environ}


def get(key, default=None):
    return ENV.get(key, default)


def require(*keys):
    missing = [k for k in keys if not ENV.get(k)]
    if missing:
        print(f"Missing required config in config/.env: {', '.join(missing)}", file=sys.stderr)
        sys.exit(2)

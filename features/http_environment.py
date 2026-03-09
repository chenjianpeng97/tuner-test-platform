from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = WORKSPACE_ROOT / "fastapi-clean-example"
BACKEND_SRC = BACKEND_ROOT / "src"

for path in (WORKSPACE_ROOT, BACKEND_ROOT, BACKEND_SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def before_all(context) -> None:
    os.environ.setdefault("APP_ENV", "local")
    context.workspace_root = WORKSPACE_ROOT
    context.backend_root = BACKEND_ROOT
    context.base_url = os.getenv("BDD_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
    context.api_base_url = f"{context.base_url}/api/v1"
    context.http = requests.Session()
    context.seeded_users = {}
    context.last_response = None
    context.last_json = None


def before_scenario(context, scenario) -> None:
    del scenario
    context.http.cookies.clear()
    context.last_response = None
    context.last_json = None


def after_all(context) -> None:
    context.http.close()
"""Export the FastAPI OpenAPI schema to openspec/contracts/app-api.openapi.json.

Usage (from workspace root or fastapi-clean-example/):
    uv run --project fastapi-clean-example python fastapi-clean-example/scripts/export_openapi.py
  OR (from fastapi-clean-example/ with cwd set):
    uv run python scripts/export_openapi.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path bootstrap: mirror what http_environment.py does so imports work.
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_ROOT = SCRIPT_DIR.parent  # fastapi-clean-example/
BACKEND_SRC = BACKEND_ROOT / "src"
WORKSPACE_ROOT = BACKEND_ROOT.parent  # repo root

for _p in (WORKSPACE_ROOT, BACKEND_ROOT, BACKEND_SRC):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

# ---------------------------------------------------------------------------
# App bootstrap
# ---------------------------------------------------------------------------
os.environ.setdefault("APP_ENV", "local")

from app.run import make_app  # noqa: E402  (after sys.path setup)

app = make_app()

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
OUTPUT_PATH = WORKSPACE_ROOT / "openspec" / "contracts" / "app-api.openapi.json"
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

schema = app.openapi()
OUTPUT_PATH.write_text(
    json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8"
)

print(f"✓ OpenAPI schema written to {OUTPUT_PATH.relative_to(WORKSPACE_ROOT)}")
print(f"  title   : {schema.get('info', {}).get('title', '?')}")
print(f"  version : {schema.get('info', {}).get('version', '?')}")
paths = list(schema.get("paths", {}).keys())
print(f"  paths   : {len(paths)}")
for p in sorted(paths):
    print(f"    {p}")

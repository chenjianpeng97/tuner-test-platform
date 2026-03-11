"""
Behave environment for UI end-to-end tests (stage: ui).

Tech stack: Python · Playwright (sync API) · Behave · Page Object Model

Lifecycle
---------
before_all     → launch Playwright + Chromium browser (one per test run).
               → in integration mode: seed shared BDD identities into DB.
before_scenario → open an isolated BrowserContext + Page (fresh cookies/storage).
after_scenario  → capture screenshot on failure, then close page + context.
after_all       → close browser and stop Playwright.
               → in integration mode: delete seeded BDD identities from DB.

Environment variables
---------------------
BASE_URL    Frontend origin to test against (default: http://localhost:5173).
E2E_MODE    "mock" (default) or "integration".
              mock        — Vite dev server + MSW handles all API calls.
              integration — Real FastAPI backend required; DB seeding is active.
HEADLESS    "true" (default) or "false" to watch the browser.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    sync_playwright,
)

# ── Python path: allow importing from workspace root ──────────────────────────
_WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_ROOT = _WORKSPACE_ROOT / "fastapi-clean-example"
_BACKEND_SRC = _BACKEND_ROOT / "src"

for _p in (_WORKSPACE_ROOT, _BACKEND_ROOT, _BACKEND_SRC):
    _ps = str(_p)
    if _ps not in sys.path:
        sys.path.insert(0, _ps)

# ── BDD identities required by UI tests ───────────────────────────────────────
_UI_IDENTITIES = ["Charlie"]


def _seed_identities() -> None:
    """Ensure shared BDD identities exist in the DB (integration mode only)."""
    from features.factories.seeding import ensure_identity  # noqa: PLC0415
    from app.domain.enums.user_role import UserRole  # noqa: PLC0415

    for name in _UI_IDENTITIES:
        ensure_identity(name)
        print(f"[env] seeded identity: {name}")


def _delete_identities() -> None:
    """Remove shared BDD identities from the DB (integration mode teardown)."""
    from features.factories.seeding import delete_identity  # noqa: PLC0415

    for name in _UI_IDENTITIES:
        try:
            delete_identity(name)
            print(f"[env] deleted identity: {name}")
        except Exception as exc:  # noqa: BLE001
            print(f"[env] warning: could not delete {name}: {exc}")


def before_all(context) -> None:
    context.base_url = os.getenv("BASE_URL", "http://localhost:5173").rstrip("/")
    context.e2e_mode = os.getenv("E2E_MODE", "mock")
    headless = os.getenv("HEADLESS", "true").lower() != "false"

    # -- Seed DB in integration mode -------------------------------------------
    if context.e2e_mode == "integration":
        _seed_identities()

    # -- Playwright browser (shared for the whole run for speed) ---------------
    context._playwright: Playwright = sync_playwright().start()
    context._browser: Browser = context._playwright.chromium.launch(headless=headless)

    # -- Screenshot output dir -------------------------------------------------
    Path("test-results").mkdir(exist_ok=True)


def before_scenario(context, scenario) -> None:
    """Create a fresh, isolated browser context + page for each scenario."""
    context.seeded_users = {}
    context._browser_context: BrowserContext = context._browser.new_context(
        base_url=context.base_url,
        ignore_https_errors=True,
    )
    context.page: Page = context._browser_context.new_page()
    context._browser_context.set_default_timeout(15_000)


def after_scenario(context, scenario) -> None:
    """Capture a screenshot if the scenario failed, then clean up."""
    if scenario.status == "failed":
        safe_name = scenario.name.replace(" ", "_").replace("/", "_")[:80]
        try:
            context.page.screenshot(path=f"test-results/ui-fail-{safe_name}.png")
        except Exception:  # noqa: BLE001
            pass  # don't mask the original failure

    context.page.close()
    context._browser_context.close()


def after_all(context) -> None:
    context._browser.close()
    context._playwright.stop()

    # -- Clean up DB identities in integration mode ----------------------------
    if context.e2e_mode == "integration":
        _delete_identities()

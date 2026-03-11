"""BasePage — shared helpers for all Page Object classes."""

from __future__ import annotations

from playwright.sync_api import Page, expect


class BasePage:
    """
    Abstract base for all page object classes.

    Each subclass owns the selectors and actions for one page (or significant
    component) of the application.  Steps delegates *all* DOM/browser concerns
    to the appropriate Page Object — steps contain no selectors.
    """

    def __init__(self, page: Page, base_url: str = "http://localhost:5173") -> None:
        self._page = page
        self._base_url = base_url.rstrip("/")

    # ── Navigation ────────────────────────────────────────────────────────────

    def navigate(self, path: str) -> None:
        """Navigate to an absolute URL built from base_url + path."""
        self._page.goto(f"{self._base_url}{path}")

    def current_url(self) -> str:
        return self._page.url

    def wait_for_url_containing(self, fragment: str, timeout: int = 10_000) -> None:
        """Wait until the current URL contains *fragment*."""
        self._page.wait_for_function(
            f"() => window.location.href.includes({fragment!r})",
            timeout=timeout,
        )

    def wait_for_exact_url(self, path: str, timeout: int = 10_000) -> None:
        """Wait until the full URL equals base_url + path."""
        self._page.wait_for_url(f"{self._base_url}{path}", timeout=timeout)

    # ── Visibility helpers ────────────────────────────────────────────────────

    def is_visible(self, selector: str) -> bool:
        return self._page.locator(selector).is_visible()

    def wait_for_visible(self, selector: str, timeout: int = 15_000) -> None:
        expect(self._page.locator(selector)).to_be_visible(timeout=timeout)

    # ── Screenshot helper ─────────────────────────────────────────────────────

    def take_screenshot(self, name: str) -> None:
        self._page.screenshot(path=f"test-results/{name}.png")

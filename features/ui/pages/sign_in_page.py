"""SignInPage — Page Object for the /sign-in route."""

from __future__ import annotations

from playwright.sync_api import expect

from .base_page import BasePage


class SignInPage(BasePage):
    """
    Encapsulates all selectors and actions for the Sign-In page.

    Selectors are intentionally pinned to ``data-testid`` attributes so that
    styling or structural refactors do not break the tests.
    """

    # ── Route ─────────────────────────────────────────────────────────────────

    PATH = "/sign-in"

    # ── Selectors ─────────────────────────────────────────────────────────────

    _USERNAME_INPUT = "[data-testid='auth-signin-username']"
    _PASSWORD_INPUT = "[data-testid='auth-signin-password']"
    _SUBMIT_BUTTON = "[data-testid='auth-signin-submit']"

    # ── Actions ───────────────────────────────────────────────────────────────

    def goto(self) -> None:
        """Navigate to the sign-in page and wait for the username field."""
        self.navigate(self.PATH)
        self.wait_for_visible(self._USERNAME_INPUT)

    def fill_username(self, username: str) -> None:
        self._page.locator(self._USERNAME_INPUT).fill(username)

    def fill_password(self, password: str) -> None:
        self._page.locator(self._PASSWORD_INPUT).fill(password)

    def submit(self) -> None:
        self._page.locator(self._SUBMIT_BUTTON).click()

    # ── Assertion helpers ─────────────────────────────────────────────────────

    def is_on_sign_in_page(self) -> bool:
        """Return True when the current URL points to the sign-in page."""
        return self.PATH in self.current_url()

    def wait_for_redirected_away(self, timeout: int = 10_000) -> None:
        """Wait until the browser has navigated away from /sign-in."""
        self._page.wait_for_function(
            f"() => !window.location.pathname.includes('{self.PATH}')",
            timeout=timeout,
        )

    def wait_until_on_sign_in(self, timeout: int = 6_000) -> None:
        """Wait until the URL stabilises *on* the sign-in page."""
        self.wait_for_url_containing(self.PATH, timeout=timeout)

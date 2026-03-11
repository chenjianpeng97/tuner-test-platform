"""UsersPage — Page Object for the /users admin route."""

from __future__ import annotations

from playwright.sync_api import Page, expect

from .base_page import BasePage


class UsersPage(BasePage):
    """
    Encapsulates all selectors and actions for the Users list page.

    All selectors are ``data-testid`` attributes to remain resilient against
    CSS/structure changes.
    """

    # ── Route ─────────────────────────────────────────────────────────────────

    PATH = "/users"

    # ── Selectors ─────────────────────────────────────────────────────────────

    _TABLE = "[data-testid='users-table']"
    _TABLE_ROW = "[data-testid='users-table-row']"
    _ROLE_FILTER = "[data-testid='users-role-filter']"
    _STATUS_FILTER = "[data-testid='users-status-filter']"
    _INVITE_BTN = "[data-testid='users-invite-btn']"

    # Row-level action selectors (suffixed with the username)
    _ROW_ACTIVATE_BTN = "[data-testid='users-row-activate-{username}']"
    _ROW_DEACTIVATE_BTN = "[data-testid='users-row-deactivate-{username}']"
    _ROW_FOR_USER = "[data-testid='users-table-row'][data-username='{username}']"
    _ROW_ROLE_CELL = "[data-testid='users-table-row'][data-username='{username}'] [data-testid='users-row-role']"
    _ROW_STATUS_CELL = "[data-testid='users-table-row'][data-username='{username}'] [data-testid='users-row-status']"

    # ── Navigation ────────────────────────────────────────────────────────────

    def goto(self) -> None:
        """
        Navigate to the users list page using SPA (client-side) navigation.

        Clicking the sidebar link avoids a full page reload which would reset
        the in-memory Zustand auth store and the MSW session state.
        If the sidebar link is not yet visible, falls back to a direct URL load.
        """
        sidebar_link = self._page.locator('a[href="/users"]').first
        try:
            sidebar_link.wait_for(state="visible", timeout=10_000)
            sidebar_link.click()
        except Exception:
            # Fallback: hard navigate (works when server persists sessions via cookie)
            self.navigate(self.PATH)

    def wait_for_table(self, timeout: int = 15_000) -> None:
        """Wait until the users table is visible in the DOM."""
        self.wait_for_visible(self._TABLE, timeout=timeout)

    # ── Table assertions ──────────────────────────────────────────────────────

    def is_table_visible(self) -> bool:
        return self.is_visible(self._TABLE)

    def row_count(self) -> int:
        """Return the number of visible data rows in the table."""
        return self._page.locator(self._TABLE_ROW).count()

    def first_row_is_visible(self) -> bool:
        return self._page.locator(self._TABLE_ROW).first.is_visible()

    def has_user_row(self, username: str) -> bool:
        """Return True if a row with the given username is visible."""
        selector = self._ROW_FOR_USER.format(username=username)
        return self._page.locator(selector).count() > 0

    # ── Filter buttons ────────────────────────────────────────────────────────

    def is_role_filter_visible(self) -> bool:
        return self.is_visible(self._ROLE_FILTER)

    def is_status_filter_visible(self) -> bool:
        return self.is_visible(self._STATUS_FILTER)

    # ── Invite button ─────────────────────────────────────────────────────────

    def is_invite_btn_visible(self) -> bool:
        return self.is_visible(self._INVITE_BTN)

    def is_invite_btn_disabled(self) -> bool:
        """Return True when the Invite button is present but not interactive."""
        btn = self._page.locator(self._INVITE_BTN)
        return btn.is_disabled()

    # Spec-aligned aliases
    def is_invite_button_visible(self) -> bool:
        return self.is_invite_btn_visible()

    def is_invite_button_disabled(self) -> bool:
        return self.is_invite_btn_disabled()

    # ── User row actions ──────────────────────────────────────────────────────

    def activate_user(self, username: str) -> None:
        """Click the activate action for the given user row."""
        selector = self._ROW_ACTIVATE_BTN.format(username=username)
        self._page.locator(selector).click()

    def deactivate_user(self, username: str) -> None:
        """Click the deactivate action for the given user row."""
        selector = self._ROW_DEACTIVATE_BTN.format(username=username)
        self._page.locator(selector).click()

    def get_user_role(self, username: str) -> str:
        """Return the role cell text for the given user row."""
        selector = self._ROW_ROLE_CELL.format(username=username)
        return self._page.locator(selector).inner_text()

    def get_user_status(self, username: str) -> str:
        """Return the status cell text for the given user row."""
        selector = self._ROW_STATUS_CELL.format(username=username)
        return self._page.locator(selector).inner_text()

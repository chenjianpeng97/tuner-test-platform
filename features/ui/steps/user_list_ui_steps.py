"""
Behave step definitions for features/ui/user_list_ui.feature.

Architecture: all DOM interaction is delegated to Page Objects.
Steps contain no CSS selectors — they read like plain English.
"""

from __future__ import annotations

from behave import given, then, when

from features.ui.pages import SignInPage, UsersPage


# ── Background ─────────────────────────────────────────────────────────────────


@given('I am signed in as "{username}" with password "{password}"')
def step_sign_in_as(context, username: str, password: str) -> None:
    sign_in = SignInPage(context.page, context.base_url)
    sign_in.goto()
    sign_in.fill_username(username)
    sign_in.fill_password(password)
    sign_in.submit()
    # Wait until we leave the sign-in page (redirect to dashboard)
    sign_in.wait_for_redirected_away(timeout=10_000)
    # Also wait for the sidebar to be fully rendered so the auth store is settled
    # before subsequent steps attempt further navigation.
    context.page.locator('[data-sidebar="sidebar"]').first.wait_for(
        state="visible", timeout=10_000
    )
    # Stash for potential reuse in later steps
    context.sign_in_page = sign_in


@given("I navigate to the users list page")
def step_navigate_users(context) -> None:
    context.users_page = UsersPage(context.page, context.base_url)
    context.users_page.goto()
    context.users_page.wait_for_table()


# ── Then — Table ──────────────────────────────────────────────────────────────


@then("the users table should be visible")
def step_table_visible(context) -> None:
    assert context.users_page.is_table_visible(), (
        "Users table was not visible on /users"
    )


@then("at least one user row should be present")
def step_at_least_one_row(context) -> None:
    assert context.users_page.first_row_is_visible(), (
        "No user rows were visible in the users table"
    )
    count = context.users_page.row_count()
    assert count >= 1, f"Expected ≥1 user rows, got {count}"


# ── Then — Filters ────────────────────────────────────────────────────────────


@then("the role filter button should be visible")
def step_role_filter_visible(context) -> None:
    assert context.users_page.is_role_filter_visible(), (
        "Role filter button was not visible"
    )


@then("the status filter button should be visible")
def step_status_filter_visible(context) -> None:
    assert context.users_page.is_status_filter_visible(), (
        "Status filter button was not visible"
    )


# ── Then — Invite button ──────────────────────────────────────────────────────


@then("the invite user button should be visible")
def step_invite_btn_visible(context) -> None:
    assert context.users_page.is_invite_btn_visible(), (
        "Invite user button was not visible"
    )


@then("the invite user button should be disabled")
def step_invite_btn_disabled(context) -> None:
    assert context.users_page.is_invite_btn_disabled(), (
        "Expected Invite user button to be disabled but it is enabled"
    )

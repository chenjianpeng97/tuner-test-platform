"""
Behave step definitions for features/ui/auth_ui.feature.

Architecture: steps are intentionally thin — all DOM interaction is delegated
to the SignInPage Page Object.  Steps contain no CSS selectors.
"""

from __future__ import annotations

from behave import given, then, when

from features.ui.pages import SignInPage


# ── Background ────────────────────────────────────────────────────────────────


@given("I open the sign-in page")
def step_open_sign_in(context) -> None:
    context.sign_in_page = SignInPage(context.page, context.base_url)
    context.sign_in_page.goto()


# ── When ──────────────────────────────────────────────────────────────────────


@when('I enter username "{username}" and password "{password}"')
def step_enter_credentials(context, username: str, password: str) -> None:
    context.sign_in_page.fill_username(username)
    context.sign_in_page.fill_password(password)


@when("I submit the login form")
def step_submit_login(context) -> None:
    context.sign_in_page.submit()


# ── Then ──────────────────────────────────────────────────────────────────────


@then("I should be redirected to the dashboard")
def step_redirected_dashboard(context) -> None:
    context.sign_in_page.wait_for_redirected_away(timeout=10_000)
    assert SignInPage.PATH not in context.page.url, (
        f"Expected to leave {SignInPage.PATH!r} but URL is still {context.page.url!r}"
    )


@then("the app navigation sidebar should be visible")
def step_sidebar_visible(context) -> None:
    sidebar = context.page.locator('[data-sidebar="sidebar"]').first
    sidebar.wait_for(state="visible", timeout=8_000)
    assert sidebar.is_visible(), "App sidebar was not visible after login"


@then("I should remain on the sign-in page")
def step_remain_sign_in(context) -> None:
    context.sign_in_page.wait_until_on_sign_in(timeout=6_000)
    assert context.sign_in_page.is_on_sign_in_page(), (
        f"Expected to stay on sign-in but URL is {context.page.url!r}"
    )

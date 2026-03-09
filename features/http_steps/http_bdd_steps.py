from __future__ import annotations

import json
from http import HTTPStatus

from behave import given, then, when

from app.domain.enums.user_role import UserRole
from features.http_steps.factories.identity_registry import get_identity
from features.http_steps.factories.seeding import (
    delete_identity,
    ensure_identity,
    get_user,
)


def _parse_role(value: str) -> UserRole:
    return UserRole(value)


def _parse_bool(value: str) -> bool:
    return value.lower() == "true"


def _json_body(response):
    if response.content:
        return response.json()
    return None


def _request(context, method: str, path: str, *, payload: dict | None = None):
    response = context.http.request(
        method=method,
        url=f"{context.api_base_url}{path}",
        json=payload,
        timeout=10,
    )
    context.last_response = response
    context.last_json = _json_body(response)
    return response


def _fetch_user(name: str):
    user = get_user(name)
    if user is None:
        raise AssertionError(f"User {name!r} was not found in the database.")
    return user


@given('the shared identity "{name}" exists as role "{role}" and is active')
def step_seed_identity_active(context, name: str, role: str) -> None:
    context.seeded_users[name] = ensure_identity(
        name,
        role=_parse_role(role),
        is_active=True,
    )


@given('the shared identity "{name}" exists as role "{role}" and is inactive')
def step_seed_identity_inactive(context, name: str, role: str) -> None:
    context.seeded_users[name] = ensure_identity(
        name,
        role=_parse_role(role),
        is_active=False,
    )


@given('no user named "{name}" exists')
def step_delete_user(context, name: str) -> None:
    del context
    delete_identity(name)


@given('I am authenticated as "{name}"')
def step_authenticate_identity(context, name: str) -> None:
    identity = get_identity(name)
    _request(
        context,
        "POST",
        "/account/login",
        payload={"username": identity.username, "password": identity.password},
    )
    if context.last_response.status_code != HTTPStatus.NO_CONTENT:
        raise AssertionError(
            f"Expected login for {name!r} to succeed, got "
            f"{context.last_response.status_code} with body {context.last_response.text!r}."
        )


@when('I create the user "{name}" with password "{password}" and role "{role}"')
def step_create_user(context, name: str, password: str, role: str) -> None:
    identity = get_identity(name)
    _request(
        context,
        "POST",
        "/users/",
        payload={
            "username": identity.username,
            "password": password,
            "role": role,
        },
    )


@when('I activate the user "{name}"')
def step_activate_user(context, name: str) -> None:
    user = _fetch_user(name)
    _request(context, "PUT", f"/users/{user.id_}/activation")


@when('I deactivate the user "{name}"')
def step_deactivate_user(context, name: str) -> None:
    user = _fetch_user(name)
    _request(context, "DELETE", f"/users/{user.id_}/activation")


@when('I grant admin role to "{name}"')
def step_grant_admin(context, name: str) -> None:
    user = _fetch_user(name)
    _request(context, "PUT", f"/users/{user.id_}/roles/admin")


@when('I log in as "{name}"')
def step_login(context, name: str) -> None:
    identity = get_identity(name)
    _request(
        context,
        "POST",
        "/account/login",
        payload={"username": identity.username, "password": identity.password},
    )


@when('I attempt to log in as "{name}" with password "{password}"')
def step_login_with_password(context, name: str, password: str) -> None:
    identity = get_identity(name)
    _request(
        context,
        "POST",
        "/account/login",
        payload={"username": identity.username, "password": password},
    )


@when('I log out')
def step_logout(context) -> None:
    _request(context, "DELETE", "/account/logout")


@then('the response status should be {status_code:d}')
def step_assert_status(context, status_code: int) -> None:
    actual = context.last_response.status_code
    if actual != status_code:
        raise AssertionError(
            f"Expected status {status_code}, got {actual} with body {context.last_response.text!r}."
        )


@then('the created user id should be returned')
def step_assert_created_user_id(context) -> None:
    payload = context.last_json
    if not isinstance(payload, dict) or "id" not in payload:
        raise AssertionError(f"Expected a JSON body with id, got {json.dumps(payload)}")


@then('the user "{name}" should appear as role "{role}" and active "{active}"')
def step_assert_user_state(context, name: str, role: str, active: str) -> None:
    del context
    user = _fetch_user(name)
    if user.role != _parse_role(role):
        raise AssertionError(f"Expected role {role!r}, got {user.role.value!r}.")
    expected_active = _parse_bool(active)
    if user.is_active != expected_active:
        raise AssertionError(
            f"Expected active={expected_active}, got active={user.is_active}."
        )


@then('the auth cookie should be issued')
def step_assert_auth_cookie_issued(context) -> None:
    access_token = context.http.cookies.get("access_token")
    if not access_token:
        raise AssertionError("Expected access_token cookie to be set.")


@then('the auth cookie should not be issued')
def step_assert_auth_cookie_missing(context) -> None:
    access_token = context.http.cookies.get("access_token")
    if access_token:
        raise AssertionError("Did not expect access_token cookie to be set.")


@then('the auth cookie should be cleared')
def step_assert_auth_cookie_cleared(context) -> None:
    access_token = context.http.cookies.get("access_token")
    if access_token:
        raise AssertionError("Expected access_token cookie to be cleared.")
    set_cookie = context.last_response.headers.get("set-cookie", "")
    if "max-age=0" not in set_cookie.lower():
        raise AssertionError(f"Expected a removal Set-Cookie header, got {set_cookie!r}.")


@then('the current session should be allowed to access the protected user list endpoint')
def step_assert_session_allowed(context) -> None:
    response = _request(context, "GET", "/users/")
    if response.status_code != HTTPStatus.OK:
        raise AssertionError(
            f"Expected protected list endpoint to return 200, got {response.status_code}."
        )


@then('the current session should be unauthorized to access the protected user list endpoint')
def step_assert_session_unauthorized(context) -> None:
    response = _request(context, "GET", "/users/")
    if response.status_code not in (HTTPStatus.UNAUTHORIZED, HTTPStatus.FORBIDDEN):
        raise AssertionError(
            "Expected protected list endpoint to reject the current session, "
            f"got {response.status_code}."
        )
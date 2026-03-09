from __future__ import annotations

from dataclasses import dataclass

from app.domain.enums.user_role import UserRole


@dataclass(frozen=True, slots=True)
class IdentitySpec:
    name: str
    username: str
    password: str
    role: UserRole
    is_active: bool


IDENTITIES: dict[str, IdentitySpec] = {
    "Alice": IdentitySpec(
        name="Alice",
        username="alice01",
        password="Alice Password 123!",
        role=UserRole.SUPER_ADMIN,
        is_active=True,
    ),
    "Bob": IdentitySpec(
        name="Bob",
        username="bobby01",
        password="Bob Password 123!",
        role=UserRole.USER,
        is_active=True,
    ),
    "Charlie": IdentitySpec(
        name="Charlie",
        username="charlie01",
        password="Charlie Password 123!",
        role=UserRole.ADMIN,
        is_active=True,
    ),
}


def get_identity(name: str) -> IdentitySpec:
    try:
        return IDENTITIES[name]
    except KeyError as err:
        available = ", ".join(sorted(IDENTITIES))
        raise KeyError(f"Unknown identity {name!r}. Available identities: {available}.") from err
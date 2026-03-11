"""Identity registry — loaded at runtime from features/fixtures/fixtures.toml.

To add or change an identity, edit ``features/fixtures/fixtures.toml`` only;
no Python changes are required.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from app.domain.enums.user_role import UserRole

# ── TOML source ───────────────────────────────────────────────────────────────
_FIXTURES_TOML = Path(__file__).resolve().parents[1] / "fixtures" / "fixtures.toml"


@dataclass(frozen=True, slots=True)
class IdentitySpec:
    name: str
    username: str
    password: str
    role: UserRole
    is_active: bool


def _load_identities() -> dict[str, IdentitySpec]:
    with _FIXTURES_TOML.open("rb") as fh:
        raw = tomllib.load(fh)
    return {
        name: IdentitySpec(
            name=name,
            username=spec["username"],
            password=spec["password"],
            role=UserRole(spec["role"]),
            is_active=spec["is_active"],
        )
        for name, spec in raw.get("users", {}).items()
    }


IDENTITIES: dict[str, IdentitySpec] = _load_identities()


def get_identity(name: str) -> IdentitySpec:
    try:
        return IDENTITIES[name]
    except KeyError as err:
        available = ", ".join(sorted(IDENTITIES))
        raise KeyError(
            f"Unknown identity {name!r}. Available identities: {available}."
        ) from err

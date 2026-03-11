# features/http_steps/factories/identity_registry.py
# Re-exports the canonical registry from features.factories so both HTTP
# BDD steps and UI BDD steps share a single TOML-backed implementation.
from features.factories.identity_registry import (  # noqa: F401
    IdentitySpec,
    IDENTITIES,
    get_identity,
)
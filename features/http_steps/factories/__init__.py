# Shared HTTP step factories.
# 向后兼容重新导出：实际实现已移至 features.factories
from features.factories.identity_registry import get_identity, IdentitySpec, IDENTITIES  # noqa: F401
from features.factories.seeding import (
    ensure_identity,
    delete_identity,
    get_user,
    SeededUser,
)  # noqa: F401

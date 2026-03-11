from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.common.exceptions.authorization import AuthorizationError
from app.application.queries.get_current_user import GetCurrentUserQueryService
from app.domain.enums.user_role import UserRole
from app.infrastructure.auth.exceptions import AuthenticationError
from tests.app.unit.factories.user_entity import create_user


@pytest.mark.asyncio
async def test_returns_current_user_data() -> None:
    # Arrange
    user = create_user(role=UserRole.ADMIN, is_active=True)
    current_user_service = MagicMock()
    current_user_service.get_current_user = AsyncMock(return_value=user)

    sut = GetCurrentUserQueryService(current_user_service)

    # Act
    result = await sut.execute()

    # Assert
    assert result.id_ == str(user.id_.value)
    assert result.username == user.username.value
    assert result.role == UserRole.ADMIN
    assert result.is_active is True


@pytest.mark.asyncio
async def test_propagates_authentication_error() -> None:
    # Arrange
    current_user_service = MagicMock()
    current_user_service.get_current_user = AsyncMock(
        side_effect=AuthenticationError("not authenticated")
    )

    sut = GetCurrentUserQueryService(current_user_service)

    # Act & Assert
    with pytest.raises(AuthenticationError):
        await sut.execute()


@pytest.mark.asyncio
async def test_propagates_authorization_error_for_inactive_user() -> None:
    # Arrange
    current_user_service = MagicMock()
    current_user_service.get_current_user = AsyncMock(
        side_effect=AuthorizationError("user inactive")
    )

    sut = GetCurrentUserQueryService(current_user_service)

    # Act & Assert
    with pytest.raises(AuthorizationError):
        await sut.execute()

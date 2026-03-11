import logging
from dataclasses import dataclass

from app.application.common.services.current_user import CurrentUserService
from app.domain.enums.user_role import UserRole

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GetCurrentUserQM:
    id_: str
    username: str
    role: UserRole
    is_active: bool


class GetCurrentUserQueryService:
    """
    - Requires authentication (valid session cookie).
    - Returns the profile of the currently logged-in user.
    """

    def __init__(self, current_user_service: CurrentUserService) -> None:
        self._current_user_service = current_user_service

    async def execute(self) -> GetCurrentUserQM:
        """
        :raises AuthenticationError:
        :raises AuthorizationError:
        :raises DataMapperError:
        """
        log.info("Get current user: started.")
        user = await self._current_user_service.get_current_user()
        log.info("Get current user: done.")
        return GetCurrentUserQM(
            id_=str(user.id_.value),
            username=user.username.value,
            role=user.role,
            is_active=user.is_active,
        )

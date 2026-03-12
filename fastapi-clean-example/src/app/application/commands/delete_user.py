import logging
from dataclasses import dataclass
from uuid import UUID

from app.application.common.ports.access_revoker import AccessRevoker
from app.application.common.ports.transaction_manager import TransactionManager
from app.application.common.ports.user_command_gateway import UserCommandGateway
from app.application.common.services.authorization.authorize import authorize
from app.application.common.services.authorization.permissions import (
    CanManageRole,
    CanManageSubordinate,
    RoleManagementContext,
    UserManagementContext,
)
from app.application.common.services.current_user import CurrentUserService
from app.domain.entities.user import User
from app.domain.enums.user_role import UserRole
from app.domain.exceptions.user import UserNotFoundByIdError
from app.domain.value_objects.user_id import UserId

log = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DeleteUserRequest:
    user_id: UUID


class DeleteUserInteractor:
    """
    - Restricted to super admins.
    - Hard-deletes a user and revokes all their active sessions.
    - Super admins cannot delete other super admins.
    """

    def __init__(
        self,
        current_user_service: CurrentUserService,
        user_command_gateway: UserCommandGateway,
        transaction_manager: TransactionManager,
        access_revoker: AccessRevoker,
    ) -> None:
        self._current_user_service = current_user_service
        self._user_command_gateway = user_command_gateway
        self._transaction_manager = transaction_manager
        self._access_revoker = access_revoker

    async def execute(self, request_data: DeleteUserRequest) -> None:
        """
        :raises AuthenticationError:
        :raises DataMapperError:
        :raises AuthorizationError:
        :raises UserNotFoundByIdError:
        """
        log.info(
            "Delete user: started. Target user ID: '%s'.",
            request_data.user_id,
        )

        current_user = await self._current_user_service.get_current_user()

        # Only super admins can delete (can manage ADMIN role → SUPER_ADMIN only)
        authorize(
            CanManageRole(),
            context=RoleManagementContext(
                subject=current_user,
                target_role=UserRole.ADMIN,
            ),
        )

        user_id = UserId(request_data.user_id)
        user: User | None = await self._user_command_gateway.read_by_id(
            user_id,
            for_update=True,
        )
        if user is None:
            raise UserNotFoundByIdError(user_id)

        authorize(
            CanManageSubordinate(),
            context=UserManagementContext(
                subject=current_user,
                target=user,
            ),
        )

        await self._access_revoker.remove_all_user_access(user.id_)
        await self._user_command_gateway.delete(user)
        await self._transaction_manager.commit()

        log.info("Delete user: done. Target user ID: '%s'.", user_id.value)

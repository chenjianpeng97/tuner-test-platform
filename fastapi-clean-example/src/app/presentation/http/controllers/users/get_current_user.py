from inspect import getdoc
from uuid import UUID

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, Security, status
from fastapi_error_map import ErrorAwareRouter, rule
from pydantic import BaseModel, ConfigDict

from app.application.common.exceptions.authorization import AuthorizationError
from app.application.queries.get_current_user import GetCurrentUserQueryService
from app.domain.enums.user_role import UserRole
from app.infrastructure.auth.exceptions import AuthenticationError
from app.infrastructure.exceptions.gateway import DataMapperError
from app.presentation.http.auth.openapi_marker import cookie_scheme
from app.presentation.http.errors.callbacks import log_error, log_info
from app.presentation.http.errors.translators import ServiceUnavailableTranslator


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(frozen=True)

    id_: UUID
    username: str
    role: UserRole
    is_active: bool


def create_get_current_user_router() -> APIRouter:
    router = ErrorAwareRouter()

    @router.get(
        "/me",
        description=getdoc(GetCurrentUserQueryService),
        error_map={
            AuthenticationError: status.HTTP_401_UNAUTHORIZED,
            AuthorizationError: status.HTTP_401_UNAUTHORIZED,
            DataMapperError: rule(
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
                translator=ServiceUnavailableTranslator(),
                on_error=log_error,
            ),
        },
        default_on_error=log_info,
        status_code=status.HTTP_200_OK,
        response_model=CurrentUserResponse,
        dependencies=[Security(cookie_scheme)],
    )
    @inject
    async def get_current_user(
        interactor: FromDishka[GetCurrentUserQueryService],
    ) -> CurrentUserResponse:
        result = await interactor.execute()
        return CurrentUserResponse(
            id_=UUID(result.id_),
            username=result.username,
            role=result.role,
            is_active=result.is_active,
        )

    return router

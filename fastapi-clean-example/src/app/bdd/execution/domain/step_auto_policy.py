from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

from app.bdd.execution.gateway.sqlalchemy_hybrid_repo import SqlalchemyHybridRepository


@dataclass(slots=True)
class StepAutoPolicy:
    repo: SqlalchemyHybridRepository

    async def record_auto_failure(
        self,
        *,
        record_id: UUID,
        message: str,
    ) -> None:
        await self.repo.append_step_error(record_id=record_id, message=message)

    async def allow_manual_override(
        self,
        *,
        record_id: UUID,
        manual_status: str,
    ) -> None:
        if manual_status != "pass":
            return
        await self.repo.append_step_error(
            record_id=record_id,
            message="auto failed; manual override allowed",
        )

    @staticmethod
    def should_allow_manual_override(keyword: str) -> bool:
        return keyword.strip().lower() == "given"

    def validate_manual_override(
        self,
        *,
        keyword: str,
        manual_status: str,
    ) -> bool:
        if manual_status != "pass":
            return True
        return self.should_allow_manual_override(keyword)

    async def ensure_override_policy(
        self,
        *,
        record_id: UUID,
        keyword: str,
        manual_status: str,
    ) -> None:
        if manual_status == "pass" and self.should_allow_manual_override(keyword):
            await self.allow_manual_override(record_id=record_id, manual_status=manual_status)

from __future__ import annotations

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.domain.entities.user import User
from app.domain.enums.user_role import UserRole
from app.domain.value_objects.raw_password import RawPassword
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.username import Username
from app.infrastructure.adapters.password_hasher_bcrypt import BcryptPasswordHasher
from app.infrastructure.persistence_sqla.mappings.all import map_tables
from app.setup.config.settings import load_settings
from features.http_steps.factories.identity_registry import get_identity

_MAPPINGS_READY = False
os.environ.setdefault("APP_ENV", "local")


@dataclass(frozen=True, slots=True)
class SeededUser:
    id_: str
    username: str
    role: UserRole
    is_active: bool


def ensure_identity(
    name: str,
    *,
    role: UserRole | None = None,
    is_active: bool | None = None,
) -> SeededUser:
    return asyncio.run(_ensure_identity(name, role=role, is_active=is_active))


def delete_identity(name: str) -> None:
    asyncio.run(_delete_identity(name))


def get_user(name: str) -> SeededUser | None:
    return asyncio.run(_get_user(name))


async def _ensure_identity(
    name: str,
    *,
    role: UserRole | None,
    is_active: bool | None,
) -> SeededUser:
    identity = get_identity(name)
    settings = load_settings()
    _ensure_mappings_ready()
    engine = _create_engine(settings)
    session_factory = _create_session_factory(engine)

    async with session_factory() as session:
        existing = await _read_user(session, identity.username)
        password_hash = _hash_password(identity.password, settings)
        if existing is None:
            user = User(
                id_=UserId(uuid4()),
                username=Username(identity.username),
                password_hash=password_hash,
                role=role or identity.role,
                is_active=identity.is_active if is_active is None else is_active,
            )
            session.add(user)
        else:
            existing.password_hash = password_hash
            existing.role = role or identity.role
            existing.is_active = identity.is_active if is_active is None else is_active
            user = existing
        await session.commit()
        await session.refresh(user)
        seeded = SeededUser(
            id_=str(user.id_.value),
            username=user.username.value,
            role=user.role,
            is_active=user.is_active,
        )

    await engine.dispose()
    return seeded


async def _delete_identity(name: str) -> None:
    identity = get_identity(name)
    settings = load_settings()
    _ensure_mappings_ready()
    engine = _create_engine(settings)
    session_factory = _create_session_factory(engine)

    async with session_factory() as session:
        existing = await _read_user(session, identity.username)
        if existing is not None:
            await session.delete(existing)
            await session.commit()

    await engine.dispose()


async def _get_user(name: str) -> SeededUser | None:
    identity = get_identity(name)
    settings = load_settings()
    _ensure_mappings_ready()
    engine = _create_engine(settings)
    session_factory = _create_session_factory(engine)

    async with session_factory() as session:
        user = await _read_user(session, identity.username)
        seeded = (
            None
            if user is None
            else SeededUser(
                id_=str(user.id_.value),
                username=user.username.value,
                role=user.role,
                is_active=user.is_active,
            )
        )

    await engine.dispose()
    return seeded


def _create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )


async def _read_user(session: AsyncSession, username: str) -> User | None:
    stmt = select(User).where(User.username == Username(username))  # type: ignore[arg-type]
    return (await session.execute(stmt)).scalar_one_or_none()


def _create_engine(settings) -> AsyncEngine:
    return create_async_engine(
        url=settings.postgres.dsn,
        echo=settings.sqla.echo,
        echo_pool=settings.sqla.echo_pool,
        pool_size=settings.sqla.pool_size,
        max_overflow=settings.sqla.max_overflow,
        connect_args={"connect_timeout": 5},
        pool_pre_ping=True,
    )


def _ensure_mappings_ready() -> None:
    global _MAPPINGS_READY
    if _MAPPINGS_READY:
        return
    map_tables()
    _MAPPINGS_READY = True


def _hash_password(raw_password: str, settings) -> bytes:
    executor = ThreadPoolExecutor(
        max_workers=settings.security.password.hasher_max_threads,
        thread_name_prefix="bdd-bcrypt",
    )
    hasher = BcryptPasswordHasher(
        pepper=settings.security.password.pepper.encode(),
        work_factor=settings.security.password.hasher_work_factor,
        executor=executor,
        semaphore=asyncio.Semaphore(settings.security.password.hasher_max_threads),
        semaphore_wait_timeout_s=settings.security.password.hasher_semaphore_wait_timeout_s,
    )
    try:
        return hasher.hash_sync(RawPassword(raw_password))
    finally:
        executor.shutdown(wait=True, cancel_futures=True)
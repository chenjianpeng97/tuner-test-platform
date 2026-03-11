from app.domain.entities.base import Entity
from app.domain.enums.user_role import UserRole
from app.domain.value_objects.email import Email
from app.domain.value_objects.phone_number import PhoneNumber
from app.domain.value_objects.user_id import UserId
from app.domain.value_objects.user_password_hash import UserPasswordHash
from app.domain.value_objects.username import Username


class User(Entity[UserId]):
    def __init__(
        self,
        *,
        id_: UserId,
        username: Username,
        password_hash: UserPasswordHash,
        role: UserRole,
        is_active: bool,
        email: Email | None = None,
        phone_number: PhoneNumber | None = None,
    ) -> None:
        super().__init__(id_=id_)
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.is_active = is_active
        self.email = email
        self.phone_number = phone_number

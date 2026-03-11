import re
from dataclasses import dataclass
from typing import ClassVar, Final

from app.domain.exceptions.base import DomainTypeError
from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, slots=True, repr=False)
class Email(ValueObject):
    """raises DomainTypeError"""

    MAX_LEN: ClassVar[Final[int]] = 320

    # Minimal RFC-5321 shape: local@domain.tld (no whitespace, at least one dot in domain)
    PATTERN: ClassVar[Final[re.Pattern[str]]] = re.compile(
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )

    value: str

    def __post_init__(self) -> None:
        """:raises DomainTypeError:"""
        self._validate_length(self.value)
        self._validate_format(self.value)

    def _validate_length(self, value: str) -> None:
        """:raises DomainTypeError:"""
        if len(value) > self.MAX_LEN:
            raise DomainTypeError(
                f"Email must not exceed {self.MAX_LEN} characters.",
            )

    def _validate_format(self, value: str) -> None:
        """:raises DomainTypeError:"""
        if not re.match(self.PATTERN, value):
            raise DomainTypeError(
                "Email must be a valid email address (e.g. user@example.com).",
            )

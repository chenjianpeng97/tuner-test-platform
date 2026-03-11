import re
from dataclasses import dataclass
from typing import ClassVar, Final

from app.domain.exceptions.base import DomainTypeError
from app.domain.value_objects.base import ValueObject


@dataclass(frozen=True, slots=True, repr=False)
class PhoneNumber(ValueObject):
    """raises DomainTypeError"""

    MAX_LEN: ClassVar[Final[int]] = 32

    # Accepts international format: optional leading +, then digits / spaces / hyphens / parentheses
    # Minimum 7 digits to exclude obviously short noise
    PATTERN: ClassVar[Final[re.Pattern[str]]] = re.compile(
        r"^\+?[\d\s\-()\[\]]{7,32}$",
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
                f"Phone number must not exceed {self.MAX_LEN} characters.",
            )

    def _validate_format(self, value: str) -> None:
        """:raises DomainTypeError:"""
        if not re.match(self.PATTERN, value):
            raise DomainTypeError(
                "Phone number must contain only digits, spaces, hyphens, "
                "parentheses and an optional leading '+'.",
            )

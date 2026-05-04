from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True)
class Ok(Generic[T]):
    value: T

    @property
    def is_ok(self) -> bool:
        return True

    @property
    def is_err(self) -> bool:
        return False

    @property
    def value_or_none(self) -> T:
        return self.value

    @property
    def error_or_none(self) -> None:
        return None

    def unwrap(self) -> T:
        return self.value

    def unwrap_or(self, default: T) -> T:
        return self.value

    def map(self, fn: callable) -> Ok:
        return Ok(fn(self.value))


@dataclass(frozen=True)
class Err(Generic[E]):
    error: E

    @property
    def is_ok(self) -> bool:
        return False

    @property
    def is_err(self) -> bool:
        return True

    @property
    def value_or_none(self) -> None:
        return None

    @property
    def error_or_none(self) -> E:
        return self.error

    def unwrap(self) -> None:
        raise ValueError(f"Called unwrap on Err: {self.error}")

    def unwrap_or(self, default: T) -> T:
        return default

    def map(self, fn: callable) -> Err:
        return self


Result = Ok[T] | Err[E]

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MovieTitle:
    value: str

    def __post_init__(self) -> None:
        normalized = " ".join(self.value.split())
        if not normalized:
            raise ValueError("Movie title cannot be empty")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

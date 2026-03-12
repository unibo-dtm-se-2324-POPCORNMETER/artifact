from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rating:
    value: int

    def __post_init__(self) -> None:
        try:
            normalized = int(self.value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Rating must be an integer") from exc
        if not 1 <= normalized <= 10:
            raise ValueError("Rating must be between 1 and 10")
        object.__setattr__(self, "value", normalized)

    def __int__(self) -> int:
        return self.value

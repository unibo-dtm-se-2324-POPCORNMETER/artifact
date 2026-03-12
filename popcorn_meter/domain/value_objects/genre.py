from __future__ import annotations

from dataclasses import dataclass


ALLOWED_GENRES = {
    "Action",
    "Adventure",
    "Animation",
    "Comedy",
    "Crime",
    "Drama",
    "Fantasy",
    "Horror",
    "Mystery",
    "Romance",
    "Sci-Fi",
    "Thriller",
}


@dataclass(frozen=True)
class Genre:
    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if normalized not in ALLOWED_GENRES:
            raise ValueError("Invalid genre")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value

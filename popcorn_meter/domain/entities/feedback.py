from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from popcorn_meter.domain.value_objects.movie_title import MovieTitle
from popcorn_meter.domain.value_objects.rating import Rating


@dataclass(frozen=True)
class Feedback:
    title: MovieTitle
    liked: Optional[bool] = None
    rating: Optional[Rating] = None
    ts: Optional[str] = None

    @classmethod
    def from_record(cls, title: str, data: dict) -> "Feedback":
        rating = data.get("rating")
        return cls(
            title=MovieTitle(title),
            liked=data.get("liked"),
            rating=Rating(rating) if rating is not None else None,
            ts=data.get("ts"),
        )

    def to_record(self) -> dict[str, object]:
        return {
            "liked": self.liked,
            "rating": int(self.rating) if self.rating is not None else None,
            "ts": self.ts,
        }

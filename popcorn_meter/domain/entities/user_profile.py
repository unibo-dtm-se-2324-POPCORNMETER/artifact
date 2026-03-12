from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from popcorn_meter.domain.entities.feedback import Feedback
from popcorn_meter.domain.value_objects.genre import Genre
from popcorn_meter.domain.value_objects.movie_title import MovieTitle
from popcorn_meter.domain.value_objects.rating import Rating


@dataclass
class UserProfile:
    user_id: int
    favorite_genres: set[Genre] = field(default_factory=set)
    watchlist: set[MovieTitle] = field(default_factory=set)
    watched: set[MovieTitle] = field(default_factory=set)
    feedback: dict[str, Feedback] = field(default_factory=dict)

    @classmethod
    def from_primitives(
        cls,
        user_id: int,
        favorite_genres: Iterable[str],
        watchlist: Iterable[str],
        watched: Iterable[str],
        feedback: dict[str, dict],
    ) -> "UserProfile":
        return cls(
            user_id=user_id,
            favorite_genres={Genre(genre) for genre in favorite_genres},
            watchlist={MovieTitle(title) for title in watchlist},
            watched={MovieTitle(title) for title in watched},
            feedback={
                str(MovieTitle(title)): Feedback.from_record(title, data)
                for title, data in feedback.items()
            },
        )

    def set_genres(self, genres: Iterable[str]) -> None:
        self.favorite_genres = {Genre(genre) for genre in genres}

    def genre_values(self) -> list[str]:
        return sorted(str(genre) for genre in self.favorite_genres)

    def add_to_watchlist(self, title: str) -> bool:
        movie_title = MovieTitle(title)
        if movie_title in self.watchlist:
            return False
        self.watchlist.add(movie_title)
        return True

    def remove_from_watchlist(self, title: str) -> bool:
        movie_title = MovieTitle(title)
        if movie_title not in self.watchlist:
            return False
        self.watchlist.remove(movie_title)
        return True

    def clear_watchlist(self) -> None:
        self.watchlist.clear()

    def watchlist_values(self) -> list[str]:
        return sorted(str(title) for title in self.watchlist)

    def add_to_watched(self, title: str) -> bool:
        movie_title = MovieTitle(title)
        if movie_title in self.watched:
            return False
        self.watched.add(movie_title)
        return True

    def remove_from_watched(self, title: str) -> bool:
        movie_title = MovieTitle(title)
        if movie_title not in self.watched:
            return False
        self.watched.remove(movie_title)
        return True

    def clear_watched(self) -> None:
        self.watched.clear()

    def watched_values(self) -> list[str]:
        return sorted(str(title) for title in self.watched)

    def record_feedback(
        self,
        title: str,
        *,
        liked: bool | None = None,
        rating: int | None = None,
        ts: str | None = None,
    ) -> Feedback:
        movie_title = MovieTitle(title)
        existing = self.feedback.get(str(movie_title))
        new_feedback = Feedback(
            title=movie_title,
            liked=liked if liked is not None else (existing.liked if existing else None),
            rating=Rating(rating) if rating is not None else (existing.rating if existing else None),
            ts=ts if ts is not None else (existing.ts if existing else None),
        )
        self.feedback[str(movie_title)] = new_feedback
        return new_feedback

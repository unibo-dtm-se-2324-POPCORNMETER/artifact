from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from popcorn_meter.application.ports import MovieInfoPort, RepoPort
from popcorn_meter.domain.factories.user_factory import UserFactory
from popcorn_meter.domain.services.recommendation_service import RecommendationService

ALL_GENRES = [
    "Action", "Adventure", "Animation", "Comedy", "Crime", "Drama", "Fantasy",
    "Horror", "Mystery", "Romance", "Sci-Fi", "Thriller",
]


@dataclass(frozen=True)
class SessionUser:
    username: str
    user_id: int


class AppService:
    """
    Application service (use cases).
    Streamlit UI should call ONLY this layer.
    """

    def __init__(self, repo: RepoPort, omdb: MovieInfoPort) -> None:
        self.repo = repo
        self.omdb = omdb
        self.recommendation_service = RecommendationService(omdb)

    # --- Auth ---
    def sign_up(self, username: str, email: str, password: str) -> bool:
        try:
            registration = UserFactory.create_registration(username, email, password)
        except ValueError:
            return False
        return self.repo.create_user(registration.username, registration.email, registration.password)

    def login(self, email: str, password: str) -> SessionUser | None:
        try:
            normalized_email = UserFactory.normalize_login_email(email)
        except ValueError:
            return None

        ok = self.repo.verify_login(normalized_email, password)
        if not ok:
            return None

        uid = self.repo.get_user_id_by_email(normalized_email)
        if uid is None:
            return None

        username = self.repo.get_username_by_email(normalized_email)
        if username is None:
            return None

        return SessionUser(username=username.strip(), user_id=uid)

    # --- Preferences ---
    def set_genres(self, user_id: int, genres: Iterable[str]) -> None:
        self.repo.set_favorite_genres(user_id, genres)

    def get_genres(self, user_id: int) -> list[str]:
        return self.repo.get_favorite_genres(user_id)

    # --- Watchlist ---
    def add_to_watchlist(self, user_id: int, title: str) -> bool:
        return self.repo.add_watchlist(user_id, title)

    def remove_from_watchlist(self, user_id: int, title: str) -> None:
        self.repo.remove_watchlist(user_id, title)

    def clear_watchlist(self, user_id: int) -> None:
        self.repo.clear_watchlist(user_id)

    def list_watchlist(self, user_id: int) -> list[str]:
        return self.repo.list_watchlist(user_id)

    # --- Watched ---
    def add_to_watched(self, user_id: int, title: str) -> bool:
        return self.repo.add_watched(user_id, title)

    def remove_from_watched(self, user_id: int, title: str) -> None:
        fn = getattr(self.repo, "remove_watched", None)
        if callable(fn):
            fn(user_id, title)
            return
        fn2 = getattr(self.repo, "remove_from_watched", None)
        if callable(fn2):
            fn2(user_id, title)

    def clear_watched(self, user_id: int) -> None:
        self.repo.clear_watched(user_id)

    def list_watched(self, user_id: int) -> list[str]:
        return self.repo.list_watched(user_id)

    # --- OMDb ---
    def fetch_movie_details(self, title: str) -> dict:
        return self.omdb.search_by_title(title)

    # --- Feedback (optional persisted) ---
    def save_feedback(
        self,
        user_id: int,
        title: str,
        liked: Optional[bool] = None,
        rating: Optional[int] = None,
        ts: Optional[str] = None,
    ) -> None:
        fn = getattr(self.repo, "save_feedback", None)
        if callable(fn):
            fn(user_id, title, liked=liked, rating=rating, ts=ts)

    def get_feedback(self, user_id: int) -> dict[str, dict]:
        fn = getattr(self.repo, "get_feedback", None)
        if callable(fn):
            return fn(user_id)
        return {}

    # --- Recommendations ---
    def recommend_titles(self, user_id: int, limit: int = 12) -> list[str]:
        fav_genres = set(self.get_genres(user_id))
        if not fav_genres:
            return []

        watched = self.list_watched(user_id)
        if not isinstance(watched, (list, tuple, set)):
            watched = []
        watched_titles = set(watched)

        wl = self.list_watchlist(user_id)
        if not isinstance(wl, (list, tuple, set)):
            wl = []
        watchlist_titles = set(wl)

        feedback = self.get_feedback(user_id)

        return self.recommendation_service.recommend_titles(
            favorite_genres=fav_genres,
            watched_titles=watched_titles,
            watchlist_titles=watchlist_titles,
            feedback=feedback,
            limit=limit,
        )

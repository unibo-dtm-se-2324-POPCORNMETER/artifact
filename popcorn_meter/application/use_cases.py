from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from popcorn_meter.application.ports import MovieInfoPort, RepoPort
from popcorn_meter.domain.entities.user_profile import UserProfile
from popcorn_meter.domain.factories.user_factory import UserFactory
from popcorn_meter.domain.value_objects.movie_title import MovieTitle
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

    def _load_profile(self, user_id: int) -> UserProfile:
        favorite_genres = self.repo.get_favorite_genres(user_id)
        if not isinstance(favorite_genres, (list, tuple, set)):
            favorite_genres = []

        watchlist = self.repo.list_watchlist(user_id)
        if not isinstance(watchlist, (list, tuple, set)):
            watchlist = []

        watched = self.repo.list_watched(user_id)
        if not isinstance(watched, (list, tuple, set)):
            watched = []

        feedback = self.get_feedback(user_id)
        if not isinstance(feedback, dict):
            feedback = {}

        return UserProfile.from_primitives(
            user_id=user_id,
            favorite_genres=favorite_genres,
            watchlist=watchlist,
            watched=watched,
            feedback=feedback,
        )

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
        profile = self._load_profile(user_id)
        profile.set_genres(genres)
        self.repo.set_favorite_genres(user_id, profile.genre_values())

    def get_genres(self, user_id: int) -> list[str]:
        return self._load_profile(user_id).genre_values()

    # --- Watchlist ---
    def add_to_watchlist(self, user_id: int, title: str) -> bool:
        profile = self._load_profile(user_id)
        try:
            added = profile.add_to_watchlist(title)
        except ValueError:
            return False
        if not added:
            return False
        return self.repo.add_watchlist(user_id, str(MovieTitle(title)))

    def remove_from_watchlist(self, user_id: int, title: str) -> None:
        try:
            normalized = str(MovieTitle(title))
        except ValueError:
            return
        profile = self._load_profile(user_id)
        profile.remove_from_watchlist(normalized)
        self.repo.remove_watchlist(user_id, normalized)

    def clear_watchlist(self, user_id: int) -> None:
        profile = self._load_profile(user_id)
        profile.clear_watchlist()
        self.repo.clear_watchlist(user_id)

    def list_watchlist(self, user_id: int) -> list[str]:
        return self._load_profile(user_id).watchlist_values()

    # --- Watched ---
    def add_to_watched(self, user_id: int, title: str) -> bool:
        profile = self._load_profile(user_id)
        try:
            added = profile.add_to_watched(title)
        except ValueError:
            return False
        if not added:
            return False
        return self.repo.add_watched(user_id, str(MovieTitle(title)))

    def remove_from_watched(self, user_id: int, title: str) -> None:
        profile = self._load_profile(user_id)
        try:
            removed = profile.remove_from_watched(title)
            normalized = str(MovieTitle(title))
        except ValueError:
            return
        if not removed:
            return
        fn = getattr(self.repo, "remove_watched", None)
        if callable(fn):
            fn(user_id, normalized)
            return
        fn2 = getattr(self.repo, "remove_from_watched", None)
        if callable(fn2):
            fn2(user_id, normalized)

    def clear_watched(self, user_id: int) -> None:
        profile = self._load_profile(user_id)
        profile.clear_watched()
        self.repo.clear_watched(user_id)

    def list_watched(self, user_id: int) -> list[str]:
        return self._load_profile(user_id).watched_values()

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
        try:
            profile = self._load_profile(user_id)
            feedback = profile.record_feedback(title, liked=liked, rating=rating, ts=ts)
        except ValueError:
            return
        fn = getattr(self.repo, "save_feedback", None)
        if callable(fn):
            record = feedback.to_record()
            fn(user_id, str(feedback.title), liked=record["liked"], rating=record["rating"], ts=record["ts"])

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

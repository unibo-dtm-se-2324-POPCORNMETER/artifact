from dataclasses import dataclass
from typing import Iterable

from popcorn_meter.infrastructure.sqlite_repo import SqliteRepo
from popcorn_meter.infrastructure.omdb_client import OmdbClient


ALL_GENRES = [
    "Action", "Adventure", "Animation", "Comedy", "Crime", "Drama", "Fantasy",
    "Horror", "Mystery", "Romance", "Sci-Fi", "Thriller"
]


@dataclass(frozen=True)
class SessionUser:
    username: str
    user_id: int


class AppService:
    """
    Application service (use cases).
    Streamlit UI should call ONLY this layer (not raw SQL).
    """

    def __init__(self, repo: SqliteRepo,omdb: OmdbClient) -> None:
        self.repo = repo
        self.omdb= omdb

    # --- Auth ---
    def sign_up(self, username: str, password: str) -> bool:
        return self.repo.create_user(username, password)

    def login(self, username: str, password: str) -> SessionUser | None:
        ok = self.repo.verify_login(username, password)
        if not ok:
            return None
        uid = self.repo.get_user_id(username)
        if uid is None:
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

    def clear_watched(self, user_id: int) -> None:
        self.repo.clear_watched(user_id)

    def list_watched(self, user_id: int) -> list[str]:
        return self.repo.list_watched(user_id)

    # --- Recommendations (simple, proposal-aligned) ---
    def recommend_titles(self, user_id: int) -> list[str]:
        fav = set(self.get_genres(user_id))
        watched = set(self.list_watched(user_id))

        # Demo catalog until OMDb integration (your teammate will replace with real movies)
        demo_catalog = [
            ("Inception", "Sci-Fi"),
            ("Interstellar", "Sci-Fi"),
            ("The Dark Knight", "Action"),
            ("Gladiator", "Action"),
            ("Titanic", "Romance"),
            ("The Notebook", "Romance"),
            ("The Conjuring", "Horror"),
            ("Knives Out", "Mystery"),
            ("Toy Story", "Animation"),
            ("The Hangover", "Comedy"),
            ("Se7en", "Crime"),
            ("The Godfather", "Drama"),
        ]

        if not fav:
            return []

        recs = [t for (t, g) in demo_catalog if g in fav and t not in watched]
        return recs
    
    def fetch_movie_details(self, title: str) -> dict:
        return self.omdb.search_by_title(title)

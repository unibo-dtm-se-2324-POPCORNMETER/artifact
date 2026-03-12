from __future__ import annotations

from typing import Protocol


class MovieInfoProvider(Protocol):
    def search_by_title(self, title: str) -> dict: ...


class RecommendationService:
    """
    Domain service for explainable recommendation scoring.
    """

    def __init__(self, movie_info: MovieInfoProvider) -> None:
        self.movie_info = movie_info

    def recommend_titles(
        self,
        favorite_genres: set[str],
        watched_titles: set[str],
        watchlist_titles: set[str],
        feedback: dict[str, dict],
        limit: int = 12,
    ) -> list[str]:
        if not favorite_genres:
            return []

        seed_titles = {
            "Inception", "Interstellar", "The Dark Knight", "Gladiator",
            "Titanic", "The Notebook", "The Conjuring",
            "Knives Out", "Toy Story", "The Hangover",
            "Se7en", "The Godfather",
        }
        candidate_pool = set(seed_titles) | set(watchlist_titles)

        liked_actors: set[str] = set()

        for title in watched_titles:
            try:
                d = self.movie_info.search_by_title(title)
            except Exception:
                continue
            if not isinstance(d, dict):
                continue
            if d.get("Response") == "False":
                continue
            actors_raw = (d.get("Actors", "") or "")
            for actor in actors_raw.split(","):
                actor = actor.strip()
                if actor:
                    liked_actors.add(actor)

        scored: list[tuple[str, float]] = []

        for title in candidate_pool:
            if title in watched_titles:
                continue

            try:
                d = self.movie_info.search_by_title(title)
            except Exception:
                continue
            if not isinstance(d, dict):
                continue
            if d.get("Response") == "False":
                continue

            score = 0.0

            genre_str = (d.get("Genre", "") or "")
            movie_genres = {g.strip() for g in genre_str.split(",") if g.strip()}
            score += 3.0 * len(favorite_genres & movie_genres)

            actors_str = (d.get("Actors", "") or "")
            movie_actors = {a.strip() for a in actors_str.split(",") if a.strip()}
            score += 2.0 * len(liked_actors & movie_actors)

            imdb_rating = (d.get("imdbRating", "0") or "0")
            try:
                rating_val = float(imdb_rating)
                if rating_val > 0:
                    score += rating_val / 2.0
            except ValueError:
                pass

            plot = (d.get("Plot", "") or "").lower()
            for genre in favorite_genres:
                if genre.lower() in plot:
                    score += 1.0

            if title in watchlist_titles:
                score += 0.5

            fb = feedback.get(title)
            if isinstance(fb, dict):
                liked = fb.get("liked", None)
                user_rating = fb.get("rating", None)

                if liked is True:
                    score += 3.0
                elif liked is False:
                    score -= 5.0

                if isinstance(user_rating, int) and 1 <= user_rating <= 10:
                    score += float(user_rating) / 2.0

            if score > 0:
                scored.append((title, score))

        scored.sort(key=lambda item: item[1], reverse=True)
        ranked = [title for title, _score in scored[: max(1, int(limit))]]
        if ranked:
            return ranked

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

        recs = [title for title, genre in demo_catalog if genre in favorite_genres and title not in watched_titles]
        return recs[: max(1, int(limit))]

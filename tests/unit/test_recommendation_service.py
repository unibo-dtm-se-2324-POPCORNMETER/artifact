from unittest import TestCase
from unittest.mock import Mock

from popcorn_meter.domain.services.recommendation_service import RecommendationService


class TestRecommendationService(TestCase):
    def test_recommend_titles_returns_empty_when_no_favorite_genres(self):
        service = RecommendationService(movie_info=Mock())

        recs = service.recommend_titles(
            favorite_genres=set(),
            watched_titles=set(),
            watchlist_titles=set(),
            feedback={},
        )

        self.assertEqual(recs, [])

    def test_recommend_titles_scores_candidates_and_excludes_watched(self):
        movie_info = Mock()
        service = RecommendationService(movie_info=movie_info)

        def fake_omdb(title):
            data = {
                "Inception": {
                    "Response": "True",
                    "Actors": "Matthew McConaughey, Someone Else",
                    "Genre": "Sci-Fi, Action",
                    "imdbRating": "8.8",
                    "Plot": "A science fiction dream-heist movie.",
                },
                "Interstellar": {
                    "Response": "True",
                    "Actors": "Matthew McConaughey, Anne Hathaway",
                    "Genre": "Sci-Fi, Adventure",
                    "imdbRating": "8.6",
                    "Plot": "A sci-fi journey through space and time.",
                },
                "Knives Out": {
                    "Response": "True",
                    "Actors": "No Match",
                    "Genre": "Sci-Fi",
                    "imdbRating": "0",
                    "Plot": "",
                },
            }
            return data.get(title, {"Response": "False", "Error": "not found"})

        movie_info.search_by_title.side_effect = fake_omdb

        recs = service.recommend_titles(
            favorite_genres={"Sci-Fi"},
            watched_titles={"Inception"},
            watchlist_titles={"Interstellar"},
            feedback={
                "Interstellar": {"liked": True, "rating": 10},
                "Knives Out": {"liked": False, "rating": None},
            },
            limit=5,
        )

        self.assertIn("Interstellar", recs)
        self.assertEqual(recs[0], "Interstellar")
        self.assertNotIn("Inception", recs)
        self.assertNotIn("Knives Out", recs)

    def test_recommend_titles_uses_demo_fallback_when_omdb_produces_no_results(self):
        movie_info = Mock()
        movie_info.search_by_title.return_value = {"Response": "False", "Error": "not found"}
        service = RecommendationService(movie_info=movie_info)

        recs = service.recommend_titles(
            favorite_genres={"Sci-Fi", "Action"},
            watched_titles={"Inception"},
            watchlist_titles=set(),
            feedback={},
            limit=5,
        )

        self.assertIn("Interstellar", recs)
        self.assertIn("The Dark Knight", recs)
        self.assertNotIn("Inception", recs)

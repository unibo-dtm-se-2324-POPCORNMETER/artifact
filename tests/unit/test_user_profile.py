from unittest import TestCase

from popcorn_meter.domain.entities.user_profile import UserProfile
from popcorn_meter.domain.value_objects.genre import Genre
from popcorn_meter.domain.value_objects.rating import Rating


class TestUserProfile(TestCase):
    def test_from_primitives_builds_profile(self):
        profile = UserProfile.from_primitives(
            user_id=1,
            favorite_genres=["Action", "Drama"],
            watchlist=["  Inception  "],
            watched=["The Matrix"],
            feedback={"Inception": {"liked": True, "rating": 9, "ts": "2026-03-13T00:00:00"}},
        )

        self.assertEqual(profile.user_id, 1)
        self.assertEqual(profile.genre_values(), ["Action", "Drama"])
        self.assertEqual(profile.watchlist_values(), ["Inception"])
        self.assertEqual(profile.watched_values(), ["The Matrix"])
        self.assertTrue(profile.feedback["Inception"].liked)
        self.assertEqual(int(profile.feedback["Inception"].rating), 9)

    def test_profile_prevents_duplicate_titles(self):
        profile = UserProfile.from_primitives(1, [], [], [], {})

        self.assertTrue(profile.add_to_watchlist("Inception"))
        self.assertFalse(profile.add_to_watchlist("Inception"))
        self.assertTrue(profile.add_to_watched("The Matrix"))
        self.assertFalse(profile.add_to_watched("The Matrix"))

    def test_profile_records_feedback_and_preserves_existing_values(self):
        profile = UserProfile.from_primitives(1, [], [], [], {})

        first = profile.record_feedback("Inception", liked=True, rating=8, ts="2026-03-13T00:00:00")
        second = profile.record_feedback("Inception", liked=None, rating=None, ts=None)

        self.assertTrue(first.liked)
        self.assertEqual(int(first.rating), 8)
        self.assertTrue(second.liked)
        self.assertEqual(int(second.rating), 8)


class TestValueObjects(TestCase):
    def test_genre_accepts_only_allowed_values(self):
        self.assertEqual(str(Genre("Action")), "Action")
        with self.assertRaises(ValueError):
            Genre("Western")

    def test_rating_validates_range(self):
        self.assertEqual(int(Rating(7)), 7)
        with self.assertRaises(ValueError):
            Rating(0)
        with self.assertRaises(ValueError):
            Rating(11)

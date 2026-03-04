import sqlite3
import tempfile
from pathlib import Path
from unittest import TestCase

from popcorn_meter.infrastructure.sqlite_repo import SqliteRepo


class TestSqliteRepo(TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        db_file = Path(self._tmp.name) / "test.db"
        self.repo = SqliteRepo(db_file)

    def tearDown(self):
        self._tmp.cleanup()

    # ------------------ Users ------------------
    def test_create_user_and_login_success(self):
        ok = self.repo.create_user("Alice", "alice@example.com", "secret")
        self.assertTrue(ok)
        self.assertTrue(self.repo.verify_login("alice@example.com", "secret"))

    def test_password_is_stored_hashed(self):
        self.repo.create_user("Alice", "alice@example.com", "secret")

        with sqlite3.connect(self.repo.db_path) as conn:
            row = conn.execute(
                "SELECT password FROM users WHERE email = ?",
                ("alice@example.com",),
            ).fetchone()

        self.assertIsNotNone(row)
        stored = str(row[0])
        self.assertNotEqual(stored, "secret")
        self.assertTrue(stored.startswith("pbkdf2_sha256$"))

    def test_verify_login_fails_for_wrong_password(self):
        self.repo.create_user("Alice", "alice@example.com", "secret")
        self.assertFalse(self.repo.verify_login("alice@example.com", "bad-secret"))

    def test_create_user_duplicate_email_fails(self):
        self.repo.create_user("Alice", "alice@example.com", "secret")
        ok = self.repo.create_user("Bob", "alice@example.com", "other")
        self.assertFalse(ok)

    def test_get_user_id_and_username(self):
        self.repo.create_user("Alice", "alice@example.com", "secret")
        uid = self.repo.get_user_id_by_email("alice@example.com")
        username = self.repo.get_username_by_email("alice@example.com")

        self.assertIsNotNone(uid)
        self.assertEqual(username, "Alice")

    # ------------------ Preferences ------------------
    def test_set_and_get_favorite_genres(self):
        self.repo.create_user("Alice", "alice@example.com", "secret")
        uid = self.repo.get_user_id_by_email("alice@example.com")

        self.repo.set_favorite_genres(uid, ["Action", "Drama", "Drama"])
        genres = self.repo.get_favorite_genres(uid)
        self.assertEqual(genres, ["Action", "Drama"])

    # ------------------ Watchlist ------------------
    def test_watchlist_add_and_list(self):
        self.repo.create_user("Alice", "alice@example.com", "secret")
        uid = self.repo.get_user_id_by_email("alice@example.com")

        self.repo.add_watchlist(uid, "Inception")
        self.repo.add_watchlist(uid, "Titanic")

        titles = self.repo.list_watchlist(uid)
        self.assertEqual(titles, ["Inception", "Titanic"])

    def test_watchlist_duplicate_fails(self):
        self.repo.create_user("Alice", "alice@example.com", "secret")
        uid = self.repo.get_user_id_by_email("alice@example.com")

        self.repo.add_watchlist(uid, "Inception")
        ok = self.repo.add_watchlist(uid, "Inception")
        self.assertFalse(ok)

    # ------------------ Watched ------------------
    def test_watched_add_and_list(self):
        self.repo.create_user("Alice", "alice@example.com", "secret")
        uid = self.repo.get_user_id_by_email("alice@example.com")

        self.repo.add_watched(uid, "Inception")
        self.repo.add_watched(uid, "Titanic")

        watched = self.repo.list_watched(uid)
        self.assertEqual(watched, ["Inception", "Titanic"])

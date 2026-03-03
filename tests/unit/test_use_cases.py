from unittest import TestCase
from unittest.mock import Mock

from popcorn_meter.application.use_cases import AppService, SessionUser


class TestUseCases(TestCase):
    # ---------- Auth ----------
    def test_sign_up_delegates_to_repo_create_user(self):
        repo = Mock()
        omdb = Mock()
        repo.create_user.return_value = True

        svc = AppService(repo=repo, omdb=omdb)
        ok = svc.sign_up("alice", "alice@example.com", "secret")

        self.assertTrue(ok)
        repo.create_user.assert_called_once_with(
            "alice", "alice@example.com", "secret"
        )

    def test_login_returns_none_if_verify_login_fails(self):
        repo = Mock()
        omdb = Mock()
        repo.verify_login.return_value = False

        svc = AppService(repo=repo, omdb=omdb)
        user = svc.login("alice@example.com", "wrong")

        self.assertIsNone(user)

    def test_login_returns_none_if_user_id_missing(self):
        repo = Mock()
        omdb = Mock()

        repo.verify_login.return_value = True
        repo.get_user_id_by_email.return_value = None

        svc = AppService(repo=repo, omdb=omdb)
        user = svc.login("alice@example.com", "secret")

        self.assertIsNone(user)

    def test_login_returns_none_if_username_missing(self):
        repo = Mock()
        omdb = Mock()

        repo.verify_login.return_value = True
        repo.get_user_id_by_email.return_value = 42
        repo.get_username_by_email.return_value = None

        svc = AppService(repo=repo, omdb=omdb)
        user = svc.login("alice@example.com", "secret")

        self.assertIsNone(user)

    def test_login_returns_session_user_on_success_and_strips_username(self):
        repo = Mock()
        omdb = Mock()

        repo.verify_login.return_value = True
        repo.get_user_id_by_email.return_value = 42
        repo.get_username_by_email.return_value = "  alice  "

        svc = AppService(repo=repo, omdb=omdb)
        user = svc.login("alice@example.com", "secret")

        self.assertEqual(user, SessionUser(username="alice", user_id=42))

    # ---------- Preferences ----------
    def test_set_genres_delegates_to_repo_set_favorite_genres(self):
        repo = Mock()
        omdb = Mock()

        svc = AppService(repo=repo, omdb=omdb)
        svc.set_genres(1, ["Action", "Drama"])

        repo.set_favorite_genres.assert_called_once()
        args, _kwargs = repo.set_favorite_genres.call_args
        self.assertEqual(args[0], 1)
        self.assertEqual(list(args[1]), ["Action", "Drama"])

    def test_get_genres_returns_repo_value(self):
        repo = Mock()
        omdb = Mock()
        repo.get_favorite_genres.return_value = ["Action"]

        svc = AppService(repo=repo, omdb=omdb)
        self.assertEqual(svc.get_genres(1), ["Action"])
        repo.get_favorite_genres.assert_called_once_with(1)

    # ---------- Watchlist ----------
    def test_add_to_watchlist_delegates_to_repo(self):
        repo = Mock()
        omdb = Mock()
        repo.add_watchlist.return_value = True

        svc = AppService(repo=repo, omdb=omdb)
        self.assertTrue(svc.add_to_watchlist(1, "Inception"))
        repo.add_watchlist.assert_called_once_with(1, "Inception")

    def test_remove_from_watchlist_delegates_to_repo(self):
        repo = Mock()
        omdb = Mock()

        svc = AppService(repo=repo, omdb=omdb)
        svc.remove_from_watchlist(1, "Inception")
        repo.remove_watchlist.assert_called_once_with(1, "Inception")

    def test_clear_watchlist_delegates_to_repo(self):
        repo = Mock()
        omdb = Mock()

        svc = AppService(repo=repo, omdb=omdb)
        svc.clear_watchlist(1)
        repo.clear_watchlist.assert_called_once_with(1)

    def test_list_watchlist_returns_repo_value(self):
        repo = Mock()
        omdb = Mock()
        repo.list_watchlist.return_value = ["Inception"]

        svc = AppService(repo=repo, omdb=omdb)
        self.assertEqual(svc.list_watchlist(1), ["Inception"])
        repo.list_watchlist.assert_called_once_with(1)

    # ---------- Watched ----------
    def test_add_to_watched_delegates_to_repo(self):
        repo = Mock()
        omdb = Mock()
        repo.add_watched.return_value = True

        svc = AppService(repo=repo, omdb=omdb)
        self.assertTrue(svc.add_to_watched(1, "Inception"))
        repo.add_watched.assert_called_once_with(1, "Inception")

    def test_clear_watched_delegates_to_repo(self):
        repo = Mock()
        omdb = Mock()

        svc = AppService(repo=repo, omdb=omdb)
        svc.clear_watched(1)
        repo.clear_watched.assert_called_once_with(1)

    def test_list_watched_returns_repo_value(self):
        repo = Mock()
        omdb = Mock()
        repo.list_watched.return_value = ["Inception"]

        svc = AppService(repo=repo, omdb=omdb)
        self.assertEqual(svc.list_watched(1), ["Inception"])
        repo.list_watched.assert_called_once_with(1)

    # ---------- Recommendations ----------
    def test_recommend_titles_empty_when_no_favorite_genres(self):
        repo = Mock()
        omdb = Mock()

        svc = AppService(repo=repo, omdb=omdb)
        svc.get_genres = Mock(return_value=[])
        svc.list_watched = Mock(return_value=[])

        self.assertEqual(svc.recommend_titles(1), [])

    def test_recommend_titles_filters_by_genre_and_excludes_watched(self):
        repo = Mock()
        omdb = Mock()

        svc = AppService(repo=repo, omdb=omdb)
        svc.get_genres = Mock(return_value=["Sci-Fi", "Action"])
        svc.list_watched = Mock(return_value=["Inception"])

        recs = svc.recommend_titles(1)

        self.assertIn("Interstellar", recs)
        self.assertIn("The Dark Knight", recs)
        self.assertNotIn("Inception", recs)

    # ---------- OMDb ----------
    def test_fetch_movie_details_delegates_to_omdb_client(self):
        repo = Mock()
        omdb = Mock()
        omdb.search_by_title.return_value = {"Title": "Inception"}

        svc = AppService(repo=repo, omdb=omdb)
        data = svc.fetch_movie_details("Inception")

        self.assertEqual(data, {"Title": "Inception"})
        omdb.search_by_title.assert_called_once_with("Inception")

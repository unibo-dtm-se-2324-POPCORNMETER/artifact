import pytest
from pathlib import Path
from popcorn_meter.infrastructure.sqlite_repo import SqliteRepo


@pytest.fixture
def repo(tmp_path):
    db_file = tmp_path / "test.db"
    return SqliteRepo(db_file)


# ------------------ Users ------------------

def test_create_user_and_login_success(repo):
    ok = repo.create_user("Alice", "alice@example.com", "secret")
    assert ok is True

    assert repo.verify_login("alice@example.com", "secret") is True


def test_create_user_duplicate_email_fails(repo):
    repo.create_user("Alice", "alice@example.com", "secret")
    ok = repo.create_user("Bob", "alice@example.com", "other")

    assert ok is False


def test_get_user_id_and_username(repo):
    repo.create_user("Alice", "alice@example.com", "secret")

    uid = repo.get_user_id_by_email("alice@example.com")
    username = repo.get_username_by_email("alice@example.com")

    assert uid is not None
    assert username == "Alice"


# ------------------ Preferences ------------------

def test_set_and_get_favorite_genres(repo):
    repo.create_user("Alice", "alice@example.com", "secret")
    uid = repo.get_user_id_by_email("alice@example.com")

    repo.set_favorite_genres(uid, ["Action", "Drama", "Drama"])

    genres = repo.get_favorite_genres(uid)
    assert genres == ["Action", "Drama"]


# ------------------ Watchlist ------------------

def test_watchlist_add_and_list(repo):
    repo.create_user("Alice", "alice@example.com", "secret")
    uid = repo.get_user_id_by_email("alice@example.com")

    repo.add_watchlist(uid, "Inception")
    repo.add_watchlist(uid, "Titanic")

    titles = repo.list_watchlist(uid)
    assert titles == ["Inception", "Titanic"]


def test_watchlist_duplicate_fails(repo):
    repo.create_user("Alice", "alice@example.com", "secret")
    uid = repo.get_user_id_by_email("alice@example.com")

    repo.add_watchlist(uid, "Inception")
    ok = repo.add_watchlist(uid, "Inception")

    assert ok is False


# ------------------ Watched ------------------

def test_watched_add_and_list(repo):
    repo.create_user("Alice", "alice@example.com", "secret")
    uid = repo.get_user_id_by_email("alice@example.com")

    repo.add_watched(uid, "Inception")
    repo.add_watched(uid, "Titanic")

    watched = repo.list_watched(uid)
    assert watched == ["Inception", "Titanic"]
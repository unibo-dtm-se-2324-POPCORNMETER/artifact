import sqlite3
from pathlib import Path
from typing import Iterable, Optional


class SqliteRepo:
    """
    Very small SQLite repository for:
    - users (username + email + password)   [plain password, as requested]
    - preferences (favorite genres)
    - watchlist
    - watched
    """

    def __init__(self, db_path: str | Path = "data/popcorn_meter.db") -> None:
        self.db_path = str(db_path)
        # Make sure parent folder exists (e.g., data/)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS preferences (
                    user_id INTEGER NOT NULL,
                    genre TEXT NOT NULL,
                    PRIMARY KEY (user_id, genre),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS watchlist (
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    PRIMARY KEY (user_id, title),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS watched (
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    PRIMARY KEY (user_id, title),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                """
            )

    # ---------- Users ----------
    def create_user(self, username: str, email: str, password: str) -> bool:
        username = username.strip()
        email = email.strip().lower()

        if not username or not email or not password:
            return False

        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO users(username, email, password) VALUES (?, ?, ?)",
                    (username, email, password),
                )
            return True
        except sqlite3.IntegrityError:
            # email already exists (UNIQUE) or other constraint issue
            return False

    def verify_login(self, email: str, password: str) -> bool:
        email = email.strip().lower()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT password FROM users WHERE email = ?",
                (email,),
            ).fetchone()
        return (row is not None) and (row[0] == password)

    def get_user_id_by_email(self, email: str) -> Optional[int]:
        email = email.strip().lower()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id FROM users WHERE email = ?",
                (email,),
            ).fetchone()
        return None if row is None else int(row[0])

    def get_username_by_email(self, email: str) -> Optional[str]:
        email = email.strip().lower()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT username FROM users WHERE email = ?",
                (email,),
            ).fetchone()
        return None if row is None else str(row[0])

    # ---------- Preferences ----------
    def set_favorite_genres(self, user_id: int, genres: Iterable[str]) -> None:
        cleaned = sorted({g.strip() for g in genres if g.strip()})
        with self._connect() as conn:
            conn.execute("DELETE FROM preferences WHERE user_id = ?", (user_id,))
            conn.executemany(
                "INSERT INTO preferences(user_id, genre) VALUES (?, ?)",
                [(user_id, g) for g in cleaned],
            )

    def get_favorite_genres(self, user_id: int) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT genre FROM preferences WHERE user_id = ? ORDER BY genre",
                (user_id,),
            ).fetchall()
        return [r[0] for r in rows]

    # ---------- Watchlist ----------
    def add_watchlist(self, user_id: int, title: str) -> bool:
        t = title.strip()
        if not t:
            return False
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO watchlist(user_id, title) VALUES (?, ?)",
                    (user_id, t),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_watchlist(self, user_id: int, title: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM watchlist WHERE user_id = ? AND title = ?",
                (user_id, title),
            )

    def clear_watchlist(self, user_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM watchlist WHERE user_id = ?", (user_id,))

    def list_watchlist(self, user_id: int) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT title FROM watchlist WHERE user_id = ? ORDER BY title",
                (user_id,),
            ).fetchall()
        return [r[0] for r in rows]

    # ---------- Watched ----------
    def add_watched(self, user_id: int, title: str) -> bool:
        t = title.strip()
        if not t:
            return False
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO watched(user_id, title) VALUES (?, ?)",
                    (user_id, t),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def clear_watched(self, user_id: int) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM watched WHERE user_id = ?", (user_id,))

    def list_watched(self, user_id: int) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT title FROM watched WHERE user_id = ? ORDER BY title",
                (user_id,),
            ).fetchall()
        return [r[0] for r in rows]
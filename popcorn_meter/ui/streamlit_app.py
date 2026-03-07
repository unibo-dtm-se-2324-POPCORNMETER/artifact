import os
import urllib.parse
from datetime import datetime

import requests
import streamlit as st

from popcorn_meter.infrastructure.omdb_client import OmdbClient
from popcorn_meter.application.use_cases import AppService, ALL_GENRES
from popcorn_meter.infrastructure.sqlite_repo import SqliteRepo

# ----------------------------
# App setup
# ----------------------------
st.set_page_config(page_title="Popcorn Meter", layout="wide")

repo = SqliteRepo("popcorn_meter.db")
omdb = OmdbClient()
app = AppService(repo, omdb)

def _resolve_tmdb_key() -> str:
    k = os.getenv("TMDB_API_KEY", "").strip()
    if k:
        return k
    try:
        k2 = st.secrets.get("TMDB_API_KEY")  # type: ignore[attr-defined]
        if k2:
            return str(k2).strip()
    except Exception:
        pass
    return ""


TMDB_KEY = _resolve_tmdb_key()

# ----------------------------
# Session state
# ----------------------------
if "session_user" not in st.session_state:
    st.session_state.session_user = None
if "last_details" not in st.session_state:
    st.session_state.last_details = {}
if "login_failed" not in st.session_state:
    st.session_state.login_failed = False
if "home_query" not in st.session_state:
    st.session_state.home_query = ""
if "rec_page" not in st.session_state:
    st.session_state.rec_page = 1
if "dismissed_recs" not in st.session_state:
    st.session_state.dismissed_recs = set()
if "current_page" not in st.session_state:
    st.session_state.current_page = None

# ---- Flash toast (survives st.rerun) ----
if "flash_toast" not in st.session_state:
    st.session_state.flash_toast = None


def queue_toast(msg: str):
    st.session_state.flash_toast = msg


if st.session_state.flash_toast:
    st.toast(st.session_state.flash_toast)
    st.session_state.flash_toast = None


# ----------------------------
# Helpers
# ----------------------------
def is_logged_in() -> bool:
    return st.session_state.session_user is not None


def require_login() -> bool:
    if not is_logged_in():
        st.warning("Please login first from the Account page.")
        return False
    return True


def safe_key(s: str) -> str:
    # Stable-ish short key segment to avoid collisions + weird characters.
    return str(abs(hash(s)))


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def fetch_details_cached(title: str) -> dict:
    title = (title or "").strip()
    if not title:
        return {}
    return app.fetch_movie_details(title)


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def fetch_trending_titles_tmdb(limit: int = 12) -> list[str]:
    """Real trending titles from TMDb. Set env var TMDB_API_KEY to enable."""
    if not TMDB_KEY:
        return []
    try:
        url = "https://api.themoviedb.org/3/trending/movie/week"
        r = requests.get(url, params={"api_key": TMDB_KEY}, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = data.get("results", [])[:limit]
        titles = []
        for m in results:
            t = (m.get("title") or "").strip()
            if t:
                titles.append(t)
        return titles
    except Exception:
        return []


def resolve_valid_title(input_title: str) -> str | None:
    q = (input_title or "").strip()
    if not q:
        return None
    d = fetch_details_cached(q)
    if not d or d.get("Response") == "False":
        return None
    t = (d.get("Title") or "").strip()
    return t or None


def imdb_to_float(x: str) -> float | None:
    try:
        if not x or x == "N/A":
            return None
        return float(x)
    except Exception:
        return None


def year_to_int(x: str) -> int | None:
    try:
        if not x or x == "N/A":
            return None
        x = str(x).split("–")[0].split("-")[0].strip()
        return int(x)
    except Exception:
        return None


def normalize_str(x: str) -> str:
    return (x or "").strip().lower()


def passes_filters(details: dict, filters: dict) -> bool:
    if not details or details.get("Response") == "False":
        return False

    rt = imdb_to_float(details.get("imdbRating", ""))
    yr = year_to_int(details.get("Year", ""))

    if filters["min_imdb"] is not None and rt is not None and rt < filters["min_imdb"]:
        return False

    if yr is not None and (yr < filters["year_min"] or yr > filters["year_max"]):
        return False

    return True


def grid_cols() -> int:
    return 4


def where_to_watch_links(title: str) -> list[tuple[str, str]]:
    q = urllib.parse.quote_plus(title)
    return [
        ("Netflix", f"https://www.netflix.com/search?q={q}"),
        ("Prime", f"https://www.amazon.com/s?k={q}&i=instant-video"),
        ("Disney+", f"https://www.disneyplus.com/search/{q}"),
        ("YouTube", f"https://www.youtube.com/results?search_query={q}+movie"),
        ("Google", f"https://www.google.com/search?q=watch+{q}"),
    ]


def record_feedback_db(user_id: int, title: str, liked: bool | None = None, rating: int | None = None):
    """
    Persist feedback in DB (recommended) + show toast.
    Falls back safely if your AppService/repo doesn't expose the method yet.
    """
    ts = datetime.utcnow().isoformat()

    # Prefer AppService if it exists
    if hasattr(app, "save_feedback") and callable(getattr(app, "save_feedback")):
        try:
            app.save_feedback(user_id, title, liked=liked, rating=rating, ts=ts)
            return
        except Exception:
            pass

    # Otherwise call repo directly if it exists
    if hasattr(repo, "save_feedback") and callable(getattr(repo, "save_feedback")):
        try:
            repo.save_feedback(user_id, title, liked=liked, rating=rating, ts=ts)
        except Exception:
            pass


# ----------------------------
# Styling
# ----------------------------
st.markdown(
    """
<style>
[data-testid="stHeader"] { background: rgba(0,0,0,0) !important; }
footer { visibility: hidden; }
.block-container { padding-top: 0.9rem; max-width: 1200px; }

.stApp {
    background: linear-gradient(180deg, #0b0b0f 0%, #0f1117 60%, #0b0b0f 100%);
    color: #ffffff;
}

h1 { font-size: 2.0rem !important; font-weight: 950 !important; margin-bottom: 0.2rem !important; }
h2 { font-size: 1.55rem !important; font-weight: 900 !important; margin-bottom: 0.3rem !important; }
h3 { font-size: 1.25rem !important; font-weight: 850 !important; }

.appbar {
    position: sticky;
    top: 0;
    z-index: 999;
    margin: -0.4rem 0 0.9rem 0;
    padding: 0.95rem 0.95rem;
    border-radius: 18px;
    background: rgba(20, 22, 31, 0.72);
    border: 1px solid rgba(255,255,255,0.08);
    backdrop-filter: blur(10px);
}
.appbar-title {
    font-size: 48px;
    font-weight: 980;
    letter-spacing: 0.2px;
    color: #e50914;
    line-height: 1.0;
}
.appbar-subtitle { font-size: 14px; color: #b9c0cc; margin-top: 7px; }
.user-pill {
    display: inline-flex; gap: 8px; align-items: center;
    padding: 6px 10px; border-radius: 999px;
    border: 1px solid rgba(255,255,255,0.12);
    background: rgba(255,255,255,0.06);
    font-size: 12px; color: #fff; font-weight: 800;
}
.user-dot { width: 8px; height: 8px; border-radius: 999px; background: #e50914; }

.card { background: #14161f; border: 1px solid #262b36; border-radius: 16px; padding: 16px; }

.hero-card{
    background: radial-gradient(1200px 260px at 20% 0%, rgba(229,9,20,0.16) 0%, rgba(20,22,31,0.92) 55%, rgba(20,22,31,0.92) 100%);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 18px;
    padding: 18px 18px;
}
.hero-title{ font-size: 18px; font-weight: 950; margin: 0; }
.hero-sub{ margin-top: 6px; font-size: 12px; color: #b9c0cc; }

div[data-baseweb="input"] input {
    background-color: #14161f !important;
    color: #fff !important;
    border: 1px solid #2a2f3a !important;
    border-radius: 14px !important;
    height: 44px !important;
}

/* Default buttons */
.stButton button {
    background: #e50914 !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.55rem 1rem !important;
    font-weight: 800 !important;
}
.stButton button:hover { filter: brightness(1.05); }

/* Secondary buttons */
.btn-secondary button{
    background: transparent !important;
    border: 1px solid #2a2f3a !important;
    color: #ffffff !important;
}

/* Icon button style */
.btn-icon button{
    padding: 0.55rem 0.75rem !important;
    border-radius: 14px !important;
    font-weight: 900 !important;
}

/* Tiles */
.movie-card {
    background: #14161f;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 16px;
    padding: 12px;
    height: 340px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: transform 120ms ease, box-shadow 120ms ease, border 120ms ease;
}
.movie-card:hover {
    transform: translateY(-2px);
    border: 1px solid rgba(255,255,255,0.18);
    box-shadow: 0 14px 34px rgba(0,0,0,0.35);
}
.poster {
    height: 210px;
    border-radius: 14px;
    background: linear-gradient(135deg, #2b2f3a 0%, #12141d 60%);
    border: 1px solid #2a2f3a;
    overflow: hidden;
}
.poster img {
    width: 100%;
    height: 210px;
    object-fit: cover;
    display: block;
}
.title { font-size: 14px; font-weight: 900; margin-top: 10px; line-height: 1.2; }
.meta { font-size: 12px; color: #b9c0cc; margin-top: 4px; }

/* Pills */
.pill {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 800;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.12);
    color: #ffffff;
    margin-right: 8px;
}
.pill-red {
    background: rgba(229, 9, 20, 0.12);
    border: 1px solid rgba(229, 9, 20, 0.30);
    color: #ffd5d8;
}

/* Dialog title */
.dlg-title{ font-size: 26px; font-weight: 950; line-height: 1.15; margin: 0 0 8px 0; }
.dlg-year{ font-weight: 900; color: #cfd6e4; }

/* Actions button sizing */
.dlg-btn button{
    height: 44px !important;
    border-radius: 14px !important;
    padding: 0.55rem 1rem !important;
    font-weight: 800 !important;
    font-size: 14px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: clip !important;
    min-width: 0 !important;
}
.dlg-btn button *{ white-space: nowrap !important; }

hr { border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 18px 0; }
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------
# UI components
# ----------------------------
def top_appbar():
    user_label = f"{st.session_state.session_user.username}" if is_logged_in() else "Guest"
    st.markdown(
        f"""
        <div class="appbar">
          <div style="display:flex; align-items:flex-start; justify-content:space-between; gap:14px;">
            <div>
              <div class="appbar-title">Popcorn Meter</div>
              <div class="appbar-subtitle">
                Personalized movie suggestions using your profile, preferences, and watch history.
              </div>
            </div>
            <div class="user-pill" style="margin-top:6px;">
              <span class="user-dot"></span>
              <span>{user_label}</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def movie_tile(title: str, meta: str = "", poster_url: str | None = None, key_prefix: str = "m"):
    poster_html = (
        f'<div class="poster"><img src="{poster_url}" alt="{title} poster" /></div>'
        if poster_url
        else '<div class="poster"></div>'
    )
    st.markdown(
        f"""
        <div class="movie-card">
            <div>
              {poster_html}
              <div class="title">{title}</div>
              <div class="meta">{meta}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="btn-secondary dlg-btn">', unsafe_allow_html=True)
    if st.button(
        "Details",
        use_container_width=True,
        key=f"{key_prefix}_details_{safe_key(title)}",
    ):
        queue_toast("Opening details…")
        show_movie_dialog(title)
    st.markdown("</div>", unsafe_allow_html=True)


def render_movie_grid(titles: list[str], key_prefix: str, max_items: int = 24):
    n = grid_cols()
    cols = st.columns(n)
    shown = 0
    for t in titles:
        dd = fetch_details_cached(t)
        if not dd or dd.get("Response") == "False":
            continue
        poster = dd.get("Poster", "")
        poster_url = poster if poster and poster != "N/A" else None
        yr = dd.get("Year", "")
        rt = dd.get("imdbRating", "")
        meta = f"{yr} • IMDb {rt}" if yr and rt and rt != "N/A" else (yr or "")
        with cols[shown % n]:
            movie_tile(dd.get("Title", t), meta=meta, poster_url=poster_url, key_prefix=key_prefix)
        shown += 1
        if shown >= max_items:
            break
    if shown == 0:
        st.info("No movies to show.")


# ----------------------------
# Remove helpers (watched fix + fallback)
# ----------------------------
def _find_exact_saved_title(saved: list[str], wanted: str) -> str | None:
    w = normalize_str(wanted)
    for s in saved or []:
        if normalize_str(s) == w:
            return s
    return None


def _call_if_exists(obj, fn_name: str, *args) -> bool:
    fn = getattr(obj, fn_name, None)
    if callable(fn):
        try:
            fn(*args)
            return True
        except Exception:
            return False
    return False


def _remove_by_rebuild(uid: int, canon_title: str, list_fn, clear_fn, add_fn) -> bool:
    before = list_fn(uid) or []
    kept = [t for t in before if normalize_str(t) != normalize_str(canon_title)]
    if len(kept) == len(before):
        return False
    clear_fn(uid)
    for t in kept:
        add_fn(uid, t)
    return True


def _remove_from_watchlist(uid: int, canon_title: str) -> bool:
    before = app.list_watchlist(uid) or []
    match = _find_exact_saved_title(before, canon_title)
    if not match:
        return False

    _call_if_exists(app, "remove_from_watchlist", uid, match) or _call_if_exists(repo, "remove_from_watchlist", uid, match)

    after = app.list_watchlist(uid) or []
    if _find_exact_saved_title(after, canon_title) is None:
        return True

    return _remove_by_rebuild(uid, canon_title, app.list_watchlist, app.clear_watchlist, app.add_to_watchlist)


def _remove_from_watched(uid: int, canon_title: str) -> bool:
    before = app.list_watched(uid) or []
    match = _find_exact_saved_title(before, canon_title)
    if not match:
        return False

    _call_if_exists(app, "remove_from_watched", uid, match) or _call_if_exists(app, "remove_watched", uid, match)
    _call_if_exists(repo, "remove_from_watched", uid, match) or _call_if_exists(repo, "remove_watched", uid, match)

    after = app.list_watched(uid) or []
    if _find_exact_saved_title(after, canon_title) is None:
        return True

    return _remove_by_rebuild(uid, canon_title, app.list_watched, app.clear_watched, app.add_to_watched)


def movie_actions_row(uid: int, canon_title: str):
    r1c1, r1c2 = st.columns(2, vertical_alignment="center")

    with r1c1:
        st.markdown('<div class="dlg-btn">', unsafe_allow_html=True)
        if st.button("Watchlist", use_container_width=True, key=f"act_wl_{safe_key(canon_title)}"):
            ok = app.add_to_watchlist(uid, canon_title)
            queue_toast("Added to Watchlist ✅" if ok else "Already in Watchlist")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with r1c2:
        st.markdown('<div class="dlg-btn">', unsafe_allow_html=True)
        if st.button("Watched", use_container_width=True, key=f"act_w_{safe_key(canon_title)}"):
            ok = app.add_to_watched(uid, canon_title)
            queue_toast("Added to Watched ✅" if ok else "Already in Watched")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    st.markdown('<div class="dlg-btn">', unsafe_allow_html=True)
    if st.button("Remove", use_container_width=True, key=f"act_rm_{safe_key(canon_title)}"):
        removed_any = _remove_from_watchlist(uid, canon_title) or _remove_from_watched(uid, canon_title)
        queue_toast("Removed ✅" if removed_any else "Not in your lists")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def feedback_block(uid: int, canon_title: str):
    st.markdown("### Your feedback (helps recommendations)")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="btn-secondary dlg-btn">', unsafe_allow_html=True)
        if st.button("👍 Like", use_container_width=True, key=f"fb_like_{safe_key(canon_title)}"):
            record_feedback_db(uid, canon_title, liked=True)
            queue_toast("Saved 👍")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="btn-secondary dlg-btn">', unsafe_allow_html=True)
        if st.button("👎 Dislike", use_container_width=True, key=f"fb_dislike_{safe_key(canon_title)}"):
            record_feedback_db(uid, canon_title, liked=False)
            queue_toast("Saved 👎")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    rating = st.slider(
        "Rate (optional)",
        min_value=1,
        max_value=10,
        value=7,
        key=f"fb_rating_{safe_key(canon_title)}",
    )
    if st.button("Save rating", use_container_width=True, key=f"fb_save_{safe_key(canon_title)}"):
        record_feedback_db(uid, canon_title, rating=int(rating))
        queue_toast("Rating saved ⭐")
        st.rerun()

    st.markdown('<div class="btn-secondary dlg-btn">', unsafe_allow_html=True)
    if st.button("Not interested (hide)", use_container_width=True, key=f"fb_hide_{safe_key(canon_title)}"):
        st.session_state.dismissed_recs.add(canon_title)
        queue_toast("Hidden from recommendations")
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def where_to_watch_block(movie_title: str, website: str | None = None):
    st.markdown("### Where to watch")
    links = where_to_watch_links(movie_title)

    r1 = st.columns(3)
    for i, (name, url) in enumerate(links[:3]):
        with r1[i]:
            st.link_button(name, url, use_container_width=True)

    r2 = st.columns(2)
    for i, (name, url) in enumerate(links[3:]):
        with r2[i]:
            st.link_button(name, url, use_container_width=True)

    if website and website != "N/A":
        st.caption("Official site:")
        st.link_button("Open website", website, use_container_width=False)


# ----------------------------
# Dialog helper
# ----------------------------
_dialog_decorator = getattr(st, "dialog", None) or getattr(st, "experimental_dialog", None)

if _dialog_decorator:

    @_dialog_decorator("Movie details")
    def show_movie_dialog(title: str):
        with st.spinner("Loading..."):
            d = fetch_details_cached(title)

        if not d or d.get("Response") == "False":
            st.error(d.get("Error", "Movie not found"))
            return

        left, right = st.columns([1, 2], vertical_alignment="top")

        with left:
            poster = d.get("Poster", "")
            if poster and poster != "N/A":
                st.image(poster, use_container_width=True)
            else:
                st.info("Poster not available.")

            st.markdown("### Quick facts")
            facts = []
            if d.get("Director") and d.get("Director") != "N/A":
                facts.append(("Director", d.get("Director")))
            if d.get("Actors") and d.get("Actors") != "N/A":
                facts.append(("Cast", d.get("Actors")))
            if d.get("Language") and d.get("Language") != "N/A":
                facts.append(("Language", d.get("Language")))
            if d.get("Country") and d.get("Country") != "N/A":
                facts.append(("Country", d.get("Country")))
            for k, v in facts[:6]:
                st.caption(f"**{k}:** {v}")

        with right:
            movie_title = (d.get("Title") or "").strip()
            year = (d.get("Year") or "").strip()
            st.markdown(
                f"""
                <div class="dlg-title">
                    {movie_title}{f" <span class='dlg-year'>({year})</span>" if year else ""}
                </div>
                """,
                unsafe_allow_html=True,
            )

            pills = []
            rt = d.get("imdbRating", "")
            rated = d.get("Rated", "")
            runtime = d.get("Runtime", "")
            if rt and rt != "N/A":
                pills.append(f'<span class="pill pill-red">IMDb {rt}</span>')
            if rated and rated != "N/A":
                pills.append(f'<span class="pill">{rated}</span>')
            if runtime and runtime != "N/A":
                pills.append(f'<span class="pill">{runtime}</span>')
            if pills:
                st.markdown(" ".join(pills), unsafe_allow_html=True)

            genre = d.get("Genre", "")
            plot = d.get("Plot", "")
            if genre and genre != "N/A":
                st.caption(genre)
            if plot and plot != "N/A":
                st.write(plot)

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            where_to_watch_block(movie_title, website=d.get("Website", ""))

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            if not is_logged_in():
                st.info("Login to save this movie to your lists and give feedback.")
            else:
                uid = st.session_state.session_user.user_id
                canon_title = (d.get("Title") or title).strip()

                st.markdown("### Actions")
                movie_actions_row(uid, canon_title)

                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                feedback_block(uid, canon_title)

else:

    def show_movie_dialog(title: str):
        st.info("Dialogs are not supported in your Streamlit version. Please update Streamlit.")


# ----------------------------
# Sidebar nav
# ----------------------------
st.sidebar.markdown("## Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Home", "Account", "Favorite Genres", "Watchlist", "Watched", "Recommendations"],
)

if st.session_state.current_page != page:
    if page != "Home":
        st.session_state.last_details = {}
    st.session_state.current_page = page

st.sidebar.markdown("---")
st.sidebar.caption("Tip: Use **Details** to add to lists and leave feedback.")


# ----------------------------
# Pages
# ----------------------------
top_appbar()

if page == "Home":
    st.markdown(
        """
        <div class="hero-card">
            <div class="hero-title">Search</div>
            <div class="hero-sub">Type a movie title, open details, and add it to your lists.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<hr>", unsafe_allow_html=True)

    c_in, c_go, c_clear = st.columns([8, 1, 1], vertical_alignment="center")
    with c_in:
        st.session_state.home_query = st.text_input(
            "",
            value=st.session_state.home_query,
            placeholder="Search by title (e.g., Titanic)",
            label_visibility="collapsed",
        )
    with c_go:
        st.markdown('<div class="btn-icon">', unsafe_allow_html=True)
        go = st.button("🔍", use_container_width=True, key="home_search_btn")
        st.markdown("</div>", unsafe_allow_html=True)
    with c_clear:
        st.markdown('<div class="btn-secondary btn-icon">', unsafe_allow_html=True)
        clear = st.button("✕", use_container_width=True, key="home_clear_btn")
        st.markdown("</div>", unsafe_allow_html=True)

    if go:
        with st.spinner("Searching..."):
            st.session_state.last_details = fetch_details_cached(st.session_state.home_query) or {}
        queue_toast("Search done ✅")
        st.rerun()

    if clear:
        st.session_state.last_details = {}
        st.session_state.home_query = ""
        queue_toast("Cleared")
        st.rerun()

    d = st.session_state.last_details
    if d:
        if d.get("Response") == "False":
            st.error(d.get("Error", "Movie not found"))
            st.session_state.last_details = {}
        else:
            show_movie_dialog((d.get("Title") or st.session_state.home_query).strip())
            st.session_state.last_details = {}

    st.markdown("<hr>", unsafe_allow_html=True)

    if is_logged_in():
        uid = st.session_state.session_user.user_id
        genres = app.get_genres(uid) or []
        if genres:
            st.subheader("Recommended for you")
            recs = app.recommend_titles(uid) or []
            recs = [t for t in recs if t not in st.session_state.dismissed_recs]
            if recs:
                render_movie_grid(recs, key_prefix="home_rec", max_items=12)
            else:
                st.info("No recommendations yet. Add a few watched movies and genres.")

            st.markdown("<hr>", unsafe_allow_html=True)
            st.subheader("Trending this week")
        else:
            st.subheader("Trending this week")
            st.info("Pick your favorite genres to unlock personalized recommendations.")
    else:
        st.subheader("Trending this week")
        st.caption("Login to get personalized recommendations.")

    trending_titles = fetch_trending_titles_tmdb(limit=12)
    if not trending_titles:
        st.info("Trending is temporarily unavailable.")
        trending_titles = ["Inception", "Interstellar", "The Dark Knight", "The Matrix", "Titanic", "Gladiator"]

    render_movie_grid(trending_titles, key_prefix="home_trend", max_items=12)

elif page == "Account":
    st.header("Account")

    if is_logged_in():
        st.markdown(
            f"""
            <div class="card">
                <h3 style="margin:0;">Welcome, {st.session_state.session_user.username}</h3>
                <div style="margin-top:6px; color:#b9c0cc; font-size:12px;">
                    Manage your lists and preferences to improve recommendations.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        if st.button("Logout", key="logout_btn"):
            st.session_state.session_user = None
            queue_toast("Logged out")
            st.rerun()
    else:
        tab1, tab2 = st.tabs(["Sign up", "Login"])

        with tab1:
            st.subheader("Create a new account")
            su_user = st.text_input("Username", key="su_user")
            su_email = st.text_input("Email", key="su_email")
            su_pw = st.text_input("Password", type="password", key="su_pw")

            if st.button("Create account", key="btn_signup"):
                ok = app.sign_up(su_user, su_email, su_pw)
                if ok:
                    st.success("Account created. Now login from the Login tab.")
                else:
                    st.error("Could not create account (email exists or fields empty).")

        with tab2:
            st.subheader("Login to your account")
            li_email = st.text_input("Email", key="li_email")
            li_pw = st.text_input("Password", type="password", key="li_pw")

            if st.button("Login", key="btn_login", use_container_width=True):
                u = app.login(li_email, li_pw)
                if u is None:
                    st.session_state.login_failed = True
                    st.error("Invalid email or password.")
                else:
                    st.session_state.login_failed = False
                    st.session_state.session_user = u
                    queue_toast("Logged in ✅")
                    st.rerun()

elif page == "Favorite Genres":
    st.header("Favorite Genres")
    if not require_login():
        st.stop()

    uid = st.session_state.session_user.user_id
    current = app.get_genres(uid)

    st.markdown(
        """
        <div class="card">
            <h3 style="margin:0;">Choose your favorite genres</h3>
            <div style="margin-top:6px; color:#b9c0cc; font-size:12px;">
                These are used to tailor your recommendations.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    selected = st.multiselect("Genres", options=ALL_GENRES, default=current)

    c1, c2 = st.columns([1, 1], vertical_alignment="center")
    with c1:
        if st.button("Save", use_container_width=True, key="genres_save_btn"):
            app.set_genres(uid, selected)
            queue_toast("Saved ✅")
            st.rerun()
    with c2:
        st.markdown('<div class="btn-secondary dlg-btn">', unsafe_allow_html=True)
        if st.button("Clear selection", use_container_width=True, key="genres_clear_btn"):
            app.set_genres(uid, [])
            queue_toast("Cleared")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif page == "Watchlist":
    st.header("Watchlist")
    if not require_login():
        st.stop()

    uid = st.session_state.session_user.user_id

    st.markdown(
        """
        <div class="card">
            <h3 style="margin:0;">Movies you want to watch</h3>
            <div style="margin-top:6px; color:#b9c0cc; font-size:12px;">
                Add titles here to track what you're planning to watch.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    q = st.text_input("Add a movie title", key="wl_add", placeholder="e.g., Inception")
    c1, c2 = st.columns([1, 1], vertical_alignment="center")

    with c1:
        if st.button("Add", use_container_width=True, key="wl_add_btn"):
            valid_title = resolve_valid_title(q)
            if not valid_title:
                st.error("Movie not found. Please enter a valid title.")
            else:
                ok = app.add_to_watchlist(uid, valid_title)
                queue_toast("Added ✅" if ok else "Already added")
                st.rerun()

    with c2:
        st.markdown('<div class="btn-secondary dlg-btn">', unsafe_allow_html=True)
        if st.button("Clear watchlist", use_container_width=True, key="wl_clear_btn"):
            app.clear_watchlist(uid)
            queue_toast("Cleared")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    items = app.list_watchlist(uid)
    st.markdown("<hr>", unsafe_allow_html=True)
    if not items:
        st.info("No movies in watchlist.")
    else:
        render_movie_grid(items, key_prefix="wl", max_items=24)

elif page == "Watched":
    st.header("Watched")
    if not require_login():
        st.stop()

    uid = st.session_state.session_user.user_id

    st.markdown(
        """
        <div class="card">
            <h3 style="margin:0;">Movies you have watched</h3>
            <div style="margin-top:6px; color:#b9c0cc; font-size:12px;">
                Your viewing history helps improve your recommendations.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

    q = st.text_input("Add watched movie title", key="watched_add", placeholder="e.g., The Matrix")
    c1, c2 = st.columns([1, 1], vertical_alignment="center")

    with c1:
        if st.button("Add", use_container_width=True, key="watched_add_btn"):
            valid_title = resolve_valid_title(q)
            if not valid_title:
                st.error("Movie not found. Please enter a valid title.")
            else:
                ok = app.add_to_watched(uid, valid_title)
                queue_toast("Added ✅" if ok else "Already added")
                st.rerun()

    with c2:
        st.markdown('<div class="btn-secondary dlg-btn">', unsafe_allow_html=True)
        if st.button("Clear watched", use_container_width=True, key="watched_clear_btn"):
            app.clear_watched(uid)
            queue_toast("Cleared")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    items = app.list_watched(uid)
    st.markdown("<hr>", unsafe_allow_html=True)
    if not items:
        st.info("No watched movies yet.")
    else:
        render_movie_grid(items, key_prefix="watched", max_items=24)

else:  # Recommendations
    st.header("Recommendations")
    if not require_login():
        st.stop()

    uid = st.session_state.session_user.user_id
    genres = app.get_genres(uid)
    watched = app.list_watched(uid)

    st.sidebar.markdown("## Recommendation filters")
    min_imdb = st.sidebar.slider("Minimum IMDb rating", 0.0, 10.0, 7.0, 0.1)
    year_min, year_max = st.sidebar.slider("Year range", 1950, datetime.now().year, (1990, datetime.now().year))
    st.sidebar.markdown("---")

    st.markdown(
        f"""
        <div class="card">
            <h3 style="margin:0;">Recommended for you</h3>
            <div style="margin-top:6px; color:#b9c0cc; font-size:12px;">
                Selected genres: {", ".join(genres) if genres else "none"} • Watched: {len(watched)} • Hidden: {len(st.session_state.dismissed_recs)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<hr>", unsafe_allow_html=True)

    if not genres:
        st.info("Choose favorite genres first.")
        st.stop()

    filters = {"min_imdb": float(min_imdb), "year_min": int(year_min), "year_max": int(year_max)}

    recs = app.recommend_titles(uid) or []
    recs = [t for t in recs if t not in st.session_state.dismissed_recs]

    filtered = []
    for title in recs:
        dd = fetch_details_cached(title)
        if not passes_filters(dd, filters):
            continue
        filtered.append(title)

    if not filtered:
        st.info("No recommendations match your filters. Try lowering the minimum rating or widening the year range.")
        st.stop()

    per_page = 12
    total = len(filtered)
    max_page = max(1, (total + per_page - 1) // per_page)
    st.session_state.rec_page = min(max(1, st.session_state.rec_page), max_page)

    cpg1, cpg2, cpg3 = st.columns([1, 2, 1], vertical_alignment="center")
    with cpg1:
        st.markdown('<div class="btn-secondary dlg-btn">', unsafe_allow_html=True)
        if st.button("◀ Prev", use_container_width=True, disabled=st.session_state.rec_page <= 1, key="rec_prev_btn"):
            st.session_state.rec_page -= 1
            queue_toast("Previous page")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with cpg2:
        st.caption(f"Page {st.session_state.rec_page} of {max_page} • Results: {total}")
    with cpg3:
        st.markdown('<div class="btn-secondary dlg-btn">', unsafe_allow_html=True)
        if st.button("Next ▶", use_container_width=True, disabled=st.session_state.rec_page >= max_page, key="rec_next_btn"):
            st.session_state.rec_page += 1
            queue_toast("Next page")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    start = (st.session_state.rec_page - 1) * per_page
    end = start + per_page
    page_titles = filtered[start:end]

    n = grid_cols()
    cols = st.columns(n)
    for i, t in enumerate(page_titles):
        dd = fetch_details_cached(t)
        if not dd or dd.get("Response") == "False":
            continue
        poster = dd.get("Poster", "")
        poster_url = poster if poster and poster != "N/A" else None
        yr = dd.get("Year", "")
        rt = dd.get("imdbRating", "")
        meta = f"{yr} • IMDb {rt}" if yr and rt and rt != "N/A" else (yr or "")
        with cols[i % n]:
            movie_tile(dd.get("Title", t), meta=meta, poster_url=poster_url, key_prefix="rec")

import streamlit as st

from popcorn_meter.infrastructure.omdb_client import OmdbClient
from popcorn_meter.application.use_cases import AppService, ALL_GENRES
from popcorn_meter.infrastructure.sqlite_repo import SqliteRepo

# ----------------------------
# App setup
# ----------------------------
st.set_page_config(page_title="Popcorn Meter", layout="wide")

# Dark theme (clean) + consistent components
st.markdown(
    """
<style>
/* Keep header but make it blend with background */
[data-testid="stHeader"] { background: rgba(0,0,0,0) !important; }

/* Ensure sidebar toggle button remains visible */
button[kind="header"] { display: inline-flex !important; }

/* Hide footer only */
footer { visibility: hidden; }

.stApp {
    background: linear-gradient(180deg, #0b0b0f 0%, #0f1117 60%, #0b0b0f 100%);
    color: #ffffff;
}
.block-container { padding-top: 1.2rem; max-width: 1200px; }

h1, h2, h3, h4 { color: #ffffff; }
.small-muted { color: #b9c0cc; font-size: 12px; }

div[data-baseweb="input"] input {
    background-color: #14161f !important;
    color: #fff !important;
    border: 1px solid #2a2f3a !important;
}
.stButton button {
    background: #e50914 !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.6rem 1rem !important;
    font-weight: 700 !important;
}
.stButton button:hover { filter: brightness(1.05); }

.card {
    background: #14161f;
    border: 1px solid #262b36;
    border-radius: 16px;
    padding: 16px;
}

.movie-card {
    background: #14161f;
    border: 1px solid #262b36;
    border-radius: 14px;
    padding: 12px;
    height: 290px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.poster {
    height: 190px;
    border-radius: 12px;
    background: linear-gradient(135deg, #2b2f3a 0%, #12141d 60%);
    border: 1px solid #2a2f3a;
    overflow: hidden;
}
.poster img {
    width: 100%;
    height: 190px;
    object-fit: cover;
    display: block;
}
.title {
    font-size: 14px;
    font-weight: 800;
    margin-top: 10px;
    line-height: 1.2;
}
.meta {
    font-size: 12px;
    color: #b9c0cc;
    margin-top: 4px;
}
.badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    background: rgba(229, 9, 20, 0.15);
    border: 1px solid rgba(229, 9, 20, 0.35);
    color: #ffb3b8;
    margin-right: 8px;
}
hr { border: none; border-top: 1px solid #252a36; margin: 18px 0; }
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------
# Helpers
# ----------------------------
def movie_tile(title: str, meta: str = "", poster_url: str | None = None) -> None:
    poster_html = (
        f'<div class="poster"><img src="{poster_url}" alt="{title} poster" /></div>'
        if poster_url
        else '<div class="poster"></div>'
    )
    st.markdown(
        f"""
        <div class="movie-card">
            {poster_html}
            <div>
                <div class="title">{title}</div>
                <div class="meta">{meta}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Repo + app service
repo = SqliteRepo("popcorn_meter.db")
omdb = OmdbClient()
app = AppService(repo, omdb)

@st.cache_data(ttl=24 * 3600)
def fetch_details_cached(title: str) -> dict:
    title = (title or "").strip()
    if not title:
        return {}
    return app.fetch_movie_details(title)

# ----------------------------
# Session state
# ----------------------------
if "session_user" not in st.session_state:
    st.session_state.session_user = None  # SessionUser | None

if "last_details" not in st.session_state:
    st.session_state.last_details = {}

def is_logged_in() -> bool:
    return st.session_state.session_user is not None

def require_login() -> bool:
    if not is_logged_in():
        st.warning("Please login first from the Account page.")
        return False
    return True

# ----------------------------
# Sidebar
# ----------------------------
st.sidebar.markdown("## Popcorn Meter")

if is_logged_in():
    st.sidebar.success(f"Hello, {st.session_state.session_user.username}")
else:
    st.sidebar.info("Guest (not logged in)")

page = st.sidebar.radio(
    "Navigate",
    ["Home", "Account", "Favorite Genres", "Watchlist", "Watched", "Recommendations"],
)

# ----------------------------
# HOME
# ----------------------------
if page == "Home":
    st.markdown(
        """
        <div class="card">
            <h1 style="margin:0; color:#e50914;">Popcorn Meter</h1>
            <p style="margin:6px 0 0 0; color:#b9c0cc;">
                Personalized movie suggestions using your profile, preferences, and watch history.
            </p>
            <div style="margin-top:10px;">
                <span class="badge">Profile</span>
                <span class="badge">Watchlist</span>
                <span class="badge">Recommendations</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    st.subheader("Search")
    q = st.text_input("Movie title", placeholder="Try: Inception, Titanic, The Matrix")

    b1, b2, b3 = st.columns([2, 2, 2])
    with b1:
        do_fetch = st.button("Fetch details", use_container_width=True)
    with b2:
        do_add = st.button("Add to Watchlist", use_container_width=True, disabled=not is_logged_in())
    with b3:
        do_remove = st.button("Remove from Watchlist", use_container_width=True, disabled=not is_logged_in())

    if do_fetch:
        try:
            details = fetch_details_cached(q)
            if not details:
                st.warning("Enter a movie title.")
                st.session_state.last_details = {}
            elif details.get("Response") == "False":
                st.error(details.get("Error", "Movie not found"))
                st.session_state.last_details = {}
            else:
                st.session_state.last_details = details
        except Exception as e:
            st.error(str(e))
            st.session_state.last_details = {}

    details = st.session_state.last_details
    target_title = (details.get("Title") if details else q).strip()

    if details:
        title = details.get("Title", "")
        year = details.get("Year", "")
        genre = details.get("Genre", "")
        plot = details.get("Plot", "")
        poster = details.get("Poster", "")

        left, right = st.columns([1, 2])
        with left:
            if poster and poster != "N/A":
                st.image(poster, use_container_width=True)
        with right:
            st.markdown(f"### {title} ({year})" if year else f"### {title}")
            if genre:
                st.caption(genre)
            if plot:
                st.write(plot)

    if do_add and is_logged_in():
        ok = app.add_to_watchlist(st.session_state.session_user.user_id, target_title)
        st.success("Added to watchlist." if ok else "Already added or empty title.")

    if do_remove and is_logged_in():
        app.remove_from_watchlist(st.session_state.session_user.user_id, target_title)
        st.success("Removed (if it existed).")

    st.markdown("<hr>", unsafe_allow_html=True)

    st.subheader("Trending Now")
    trending = ["Inception", "Interstellar", "The Dark Knight", "The Matrix", "Titanic", "Gladiator"]
    cols = st.columns(6)
    for i, t in enumerate(trending):
        with cols[i % 6]:
            d = fetch_details_cached(t)
            poster_url = None
            if d and d.get("Response") != "False":
                p = d.get("Poster")
                poster_url = p if p and p != "N/A" else None
            movie_tile(t, meta="", poster_url=poster_url)

    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader("Your Watchlist")
    if not is_logged_in():
        st.info("Login to see your saved watchlist.")
    else:
        items = app.list_watchlist(st.session_state.session_user.user_id)
        if not items:
            st.info("Your watchlist is empty. Add a movie above.")
        else:
            cols2 = st.columns(6)
            for i, t in enumerate(items[:12]):
                with cols2[i % 6]:
                    d = fetch_details_cached(t)
                    poster_url = None
                    if d and d.get("Response") != "False":
                        p = d.get("Poster")
                        poster_url = p if p and p != "N/A" else None
                    movie_tile(t, meta="", poster_url=poster_url)

# ----------------------------
# ACCOUNT
# ----------------------------
elif page == "Account":
    st.header("Account")

    if is_logged_in():
        st.markdown(
            f"""
            <div class="card">
                <h3 style="margin:0;">Welcome, {st.session_state.session_user.username}</h3>
                <p class="small-muted" style="margin-top:6px;">
                    You can manage your preferences, watchlist and watched movies.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("Logout"):
            st.session_state.session_user = None
            st.success("Logged out.")
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

            if st.button("Login", key="btn_login"):
                u = app.login(li_email, li_pw)
                if u is None:
                    st.error("Invalid email or password.")
                else:
                    st.session_state.session_user = u
                    st.success(f"Welcome back, {u.username}!")
                    st.rerun()

# ----------------------------
# FAVORITE GENRES
# ----------------------------
elif page == "Favorite Genres":
    st.header("Favorite Genres")
    if not require_login():
        st.stop()

    uid = st.session_state.session_user.user_id
    current = app.get_genres(uid)

    st.caption("Select genres you like. Recommendations use this + watched history.")
    selected = st.multiselect("Genres", options=ALL_GENRES, default=current)

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Save Genres", use_container_width=True):
            app.set_genres(uid, selected)
            st.success("Saved.")
    with col2:
        st.info("Tip: Add watched movies to refine recommendations.")

# ----------------------------
# WATCHLIST
# ----------------------------
elif page == "Watchlist":
    st.header("Watchlist")
    if not require_login():
        st.stop()

    uid = st.session_state.session_user.user_id

    st.caption("Titles you plan to watch later.")
    q = st.text_input("Add a movie title", key="wl_add", placeholder="e.g., Inception")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Add", use_container_width=True):
            ok = app.add_to_watchlist(uid, q)
            st.success("Added." if ok else "Already added or empty title.")
    with col2:
        if st.button("Clear Watchlist", use_container_width=True):
            app.clear_watchlist(uid)
            st.success("Cleared.")

    st.markdown("<hr>", unsafe_allow_html=True)

    items = app.list_watchlist(uid)
    if not items:
        st.info("No movies in watchlist.")
    else:
        st.subheader("Your watchlist")
        for title in items:
            r1, r2 = st.columns([6, 2])
            with r1:
                st.write(title)
            with r2:
                if st.button("Remove", key=f"rm_wl_{title}", use_container_width=True):
                    app.remove_from_watchlist(uid, title)
                    st.rerun()

# ----------------------------
# WATCHED
# ----------------------------
elif page == "Watched":
    st.header("Watched History")
    if not require_login():
        st.stop()

    uid = st.session_state.session_user.user_id
    st.caption("Watched movies are excluded from recommendations.")

    q = st.text_input("Add watched movie title", key="watched_add", placeholder="e.g., The Matrix")

    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Add Watched", use_container_width=True):
            ok = app.add_to_watched(uid, q)
            st.success("Added." if ok else "Already added or empty title.")
    with col2:
        if st.button("Clear Watched", use_container_width=True):
            app.clear_watched(uid)
            st.success("Cleared.")

    st.markdown("<hr>", unsafe_allow_html=True)

    items = app.list_watched(uid)
    if not items:
        st.info("No watched movies yet.")
    else:
        st.subheader("Watched")
        for t in items:
            st.write(t)

# ----------------------------
# RECOMMENDATIONS
# ----------------------------
else:
    st.header("Recommendations")
    if not require_login():
        st.stop()

    uid = st.session_state.session_user.user_id
    genres = app.get_genres(uid)
    watched = app.list_watched(uid)

    st.markdown(
        f"""
<div class="card">
  <div><span class="badge">Genres: {", ".join(genres) if genres else "none"}</span></div>
  <div style="margin-top:8px;" class="small-muted">
    Watched titles excluded: {len(watched)}
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    if not genres:
        st.info("Choose favorite genres first.")
        st.stop()

    recs = app.recommend_titles(uid)
    if not recs:
        st.info("No recommendations found. Try adding genres or clearing watched list.")
    else:
        st.subheader("Recommended for you")
        cols = st.columns(6)
        for i, title in enumerate(recs[:12]):
            with cols[i % 6]:
                d = fetch_details_cached(title)
                poster_url = None
                if d and d.get("Response") != "False":
                    p = d.get("Poster")
                    poster_url = p if p and p != "N/A" else None
                movie_tile(title, meta="", poster_url=poster_url)
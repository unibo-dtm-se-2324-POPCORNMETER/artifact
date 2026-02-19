import streamlit as st


from popcorn_meter.infrastructure.omdb_client import OmdbClient
from popcorn_meter.application.use_cases import AppService, ALL_GENRES
from popcorn_meter.infrastructure.sqlite_repo import SqliteRepo

# ----------------------------
# Setup
# ----------------------------
st.set_page_config(page_title="Popcorn Meter", page_icon="🍿", layout="wide")

# Hide Streamlit header + apply dark theme (keeps your Netflix-ish styling)
st.markdown(
    """
<style>
[data-testid="stHeader"] { background: rgba(0,0,0,0); }
header { visibility: hidden; }
footer { visibility: hidden; }

.stApp {
    background: linear-gradient(180deg, #0b0b0f 0%, #0f1117 60%, #0b0b0f 100%);
    color: #ffffff;
}
.block-container { padding-top: 1.2rem; }
h1, h2, h3, h4 { color: #ffffff; }

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

.movie-card {
    background: #14161f;
    border: 1px solid #262b36;
    border-radius: 14px;
    padding: 12px;
    height: 260px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.poster {
    height: 170px;
    border-radius: 12px;
    background: linear-gradient(135deg, #2b2f3a 0%, #12141d 60%);
    border: 1px solid #2a2f3a;
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
}
hr { border: none; border-top: 1px solid #252a36; margin: 18px 0; }
</style>
""",
    unsafe_allow_html=True,
)

def movie_card(title: str, meta: str = ""):
    st.markdown(
        f"""
        <div class="movie-card">
            <div class="poster"></div>
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
app = AppService(repo,omdb)


# Session
if "session_user" not in st.session_state:
    st.session_state.session_user = None  # SessionUser | None


def require_login() -> bool:
    if st.session_state.session_user is None:
        st.warning("Please login first (Account page).")
        return False
    return True


# ----------------------------
# Sidebar navigation
# ----------------------------
st.sidebar.markdown("## 🍿 Popcorn Meter")

if st.session_state.session_user:
    st.sidebar.success(f"Logged in: {st.session_state.session_user.username}")
else:
    st.sidebar.info("Guest (not logged in)")

page = st.sidebar.radio(
    "Navigate",
    ["Home", "Account", "Favorite Genres", "Watchlist", "Watched", "Recommendations"],
)
st.sidebar.caption("SQLite persistence enabled (Phase: all-in-one)")

# ----------------------------
# HOME (Search + tiles)
# ----------------------------
if page == "Home":
    st.markdown(
        """
        <div style="padding: 18px; background: rgba(20,22,31,0.7);
                    border: 1px solid #262b36; border-radius: 16px;">
            <h1 style="margin:0;">🍿 Popcorn Meter</h1>
            <p style="margin:6px 0 0 0; color:#b9c0cc;">
                Personalized movie suggestions based on your profile, preferences, and history.
            </p>
            <div style="margin-top:10px;">
                <span class="badge">Home</span>
                <span class="badge" style="margin-left:8px;">Trending (demo)</span>
                <span class="badge" style="margin-left:8px;">Watchlist</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<hr>", unsafe_allow_html=True)

    st.subheader("Search & Add (Phase 1: title-only)")
    st.caption("Your teammate will integrate OMDb here to show posters/details.")
    q = st.text_input("Movie title", placeholder="Try: Inception, Titanic, The Matrix")

#adding the button for OMDb test    
    if st.button("🔎 Fetch OMDb details", use_container_width=True):
        try:
            details = app.fetch_movie_details(q)
            if details.get("Response") == "False":
                st.error(details.get("Error", "Movie not found"))
            else:
                st.success(f"{details.get('Title')} ({details.get('Year')})")
                st.write(details.get("Genre"))
                st.write(details.get("Plot"))
                poster = details.get("Poster")
                if poster and poster != "N/A":
                    st.image(poster, width=220)
                st.json(details)
        except Exception as e:
            st.error(str(e))


    if st.session_state.session_user is None:
        st.info("Login to save watchlist to the database.")
    else:
        if st.button("➕ Add to Watchlist", use_container_width=True):
            ok = app.add_to_watchlist(st.session_state.session_user.user_id, q)
            if ok:
                st.success("Added.")
            else:
                st.info("Already added or empty title.")

    st.markdown("<hr>", unsafe_allow_html=True)

    st.subheader("🔥 Trending Now (demo tiles)")
    trending = ["Inception", "Interstellar", "The Dark Knight", "The Matrix", "Titanic", "Gladiator"]
    cols = st.columns(6)
    for i, t in enumerate(trending):
        with cols[i % 6]:
            movie_card(t, meta="Posters will appear with OMDb integration")

# ----------------------------
# ACCOUNT (Signup/Login/Logout)
# ----------------------------
elif page == "Account":
    st.header("👤 Account")

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Sign up")
        su_user = st.text_input("New username", key="su_user")
        su_pw = st.text_input("Password", type="password", key="su_pw")
        if st.button("Create account"):
            ok = app.sign_up(su_user, su_pw)
            if ok:
                st.success("Account created. Now login.")
            else:
                st.error("Could not create account (maybe username exists or fields empty).")

    with c2:
        st.subheader("Login")
        li_user = st.text_input("Username", key="li_user")
        li_pw = st.text_input("Password", type="password", key="li_pw")
        if st.button("Login"):
            u = app.login(li_user, li_pw)
            if u is None:
                st.error("Invalid username or password.")
            else:
                st.session_state.session_user = u
                st.success(f"Logged in as {u.username}")
                st.rerun()

    st.markdown("<hr>", unsafe_allow_html=True)
    if st.session_state.session_user:
        if st.button("Logout"):
            st.session_state.session_user = None
            st.success("Logged out.")
            st.rerun()

# ----------------------------
# FAVORITE GENRES
# ----------------------------
elif page == "Favorite Genres":
    st.header("🎛️ Favorite Genres")
    if not require_login():
        st.stop()

    uid = st.session_state.session_user.user_id
    current = app.get_genres(uid)

    selected = st.multiselect("Select genres", options=ALL_GENRES, default=current)

    if st.button("Save Genres"):
        app.set_genres(uid, selected)
        st.success("Saved.")

# ----------------------------
# WATCHLIST
# ----------------------------
elif page == "Watchlist":
    st.header("⭐ Watchlist")
    if not require_login():
        st.stop()

    uid = st.session_state.session_user.user_id

    q = st.text_input("Add a movie title")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ Add"):
            ok = app.add_to_watchlist(uid, q)
            if ok:
                st.success("Added.")
            else:
                st.info("Already added or empty title.")
    with c2:
        if st.button("🧹 Clear"):
            app.clear_watchlist(uid)
            st.success("Cleared.")

    st.markdown("<hr>", unsafe_allow_html=True)

    items = app.list_watchlist(uid)
    if not items:
        st.info("No movies in watchlist.")
    else:
        st.write("Remove a title:")
        for title in items:
            r1, r2 = st.columns([6, 1])
            with r1:
                st.write(f"• {title}")
            with r2:
                if st.button("Remove", key=f"rm_{title}"):
                    app.remove_from_watchlist(uid, title)
                    st.rerun()

# ----------------------------
# WATCHED
# ----------------------------
elif page == "Watched":
    st.header("✅ Watched")
    if not require_login():
        st.stop()

    uid = st.session_state.session_user.user_id
    q = st.text_input("Add watched movie title")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("➕ Add watched"):
            ok = app.add_to_watched(uid, q)
            if ok:
                st.success("Added.")
            else:
                st.info("Already added or empty title.")
    with c2:
        if st.button("🧹 Clear watched"):
            app.clear_watched(uid)
            st.success("Cleared.")

    st.markdown("<hr>", unsafe_allow_html=True)
    items = app.list_watched(uid)
    if not items:
        st.info("No watched movies yet.")
    else:
        for t in items:
            st.write(f"• {t}")

# ----------------------------
# RECOMMENDATIONS
# ----------------------------
else:
    st.header("🎬 Recommendations")
    if not require_login():
        st.stop()

    uid = st.session_state.session_user.user_id
    recs = app.recommend_titles(uid)

    if not recs:
        st.info("No recommendations. Save favorite genres and/or mark watched movies.")
    else:
        st.subheader("Recommended for you (demo tiles)")
        cols = st.columns(6)
        for i, title in enumerate(recs[:12]):
            with cols[i % 6]:
                movie_card(title, meta="Rule-based (Phase 1). OMDb details in Phase 2.")

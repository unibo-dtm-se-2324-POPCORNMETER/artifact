import streamlit as st

# ----------------------------
# Phase 1: UI + Watchlist
# ----------------------------

st.set_page_config(page_title="Popcorn Meter", page_icon="🍿", layout="wide")
st.write(" Streamlit UI is working")

# Netflix-ish dark theme + tiles
st.markdown(
    """
<style>
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
    unsafe_allow_html=True
)

# ----------------------------
# Helpers
# ----------------------------
def init_state():
    if "watchlist" not in st.session_state:
        st.session_state.watchlist = []  # list of strings for Phase 1


def movie_card(title: str, meta: str = ""):
    """Netflix-like tile (poster is placeholder for Phase 1)."""
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
        unsafe_allow_html=True
    )


def add_to_watchlist(movie_title: str):
    title = movie_title.strip()
    if not title:
        st.warning("Please enter a movie title.")
        return
    if title in st.session_state.watchlist:
        st.info("Already in your watchlist.")
        return
    st.session_state.watchlist.append(title)
    st.success(f"Added: {title}")


def clear_watchlist():
    st.session_state.watchlist = []
    st.success("Watchlist cleared.")


def remove_from_watchlist(title: str):
    st.session_state.watchlist = [m for m in st.session_state.watchlist if m != title]
    st.success(f"Removed: {title}")


# ----------------------------
# App start
# ----------------------------
init_state()

# Sidebar navigation (Phase 1)
st.sidebar.markdown("## 🍿 Popcorn Meter")
page = st.sidebar.radio("Navigate", ["Home", "Watchlist"])
st.sidebar.caption("Phase 1: UI + Watchlist")

# ----------------------------
# HOME PAGE (Netflix-like)
# ----------------------------
if page == "Home":
    st.markdown(
        """
        <div style="padding: 18px; background: rgba(20,22,31,0.7);
                    border: 1px solid #262b36; border-radius: 16px;">
            <h1 style="margin:0;">🍿 Popcorn Meter</h1>
            <p style="margin:6px 0 0 0; color:#b9c0cc;">
                Find your next favorite movie that matches your vibe.
            </p>
            <div style="margin-top:10px;">
                <span class="badge">Home</span>
                <span class="badge" style="margin-left:8px;">Trending (demo)</span>
                <span class="badge" style="margin-left:8px;">Watchlist</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<hr>", unsafe_allow_html=True)

    # Add section
    st.subheader("Search & Add")
    q = st.text_input("Movie title", placeholder="Try: Inception, Titanic, The Matrix")

    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("➕ Add to Watchlist", use_container_width=True):
            add_to_watchlist(q)
    with c2:
        if st.button("🧹 Clear Watchlist", use_container_width=True):
            clear_watchlist()

    st.markdown("<hr>", unsafe_allow_html=True)

    # Trending demo tiles
    st.subheader("🔥 Trending Now (demo tiles)")
    trending = ["Inception", "Interstellar", "The Dark Knight", "The Matrix", "Titanic", "Gladiator"]
    cols = st.columns(6)
    for i, t in enumerate(trending):
        with cols[i % 6]:
            movie_card(t, meta="Posters will appear in Phase 2 (OMDb)")

    st.markdown("<br>", unsafe_allow_html=True)

    # Watchlist preview as tiles
    st.subheader("⭐ Your Watchlist (quick view)")
    if not st.session_state.watchlist:
        st.info("Your watchlist is empty. Add a movie above.")
    else:
        cols2 = st.columns(6)
        for i, t in enumerate(st.session_state.watchlist[:12]):
            with cols2[i % 6]:
                movie_card(t, meta="Saved")

# ----------------------------
# WATCHLIST PAGE (View + Remove)
# ----------------------------
else:
    st.markdown("## 🎞️ Watchlist")

    if not st.session_state.watchlist:
        st.info("No movies yet. Go to Home and add one.")
    else:
        st.write("Click remove to delete a movie from your watchlist:")
        for title in list(st.session_state.watchlist):
            row1, row2 = st.columns([6, 1])
            with row1:
                st.write(f"• {title}")
            with row2:
                if st.button("Remove", key=f"rm_{title}"):
                    remove_from_watchlist(title)
                    st.rerun()

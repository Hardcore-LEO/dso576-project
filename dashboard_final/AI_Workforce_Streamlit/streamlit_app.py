"""Streamlit launcher for the AI Workforce Investment Planner.

Run from the repository root with:
    streamlit run dashboard_final/streamlit_app.py
"""

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


APP_DIR = Path(__file__).resolve().parent
DASHBOARD_FILE = APP_DIR / "AI_Workforce_Investment_Planner.html"


st.set_page_config(
    page_title="AI Workforce Investment Planner",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Give the embedded desktop dashboard the full Streamlit content width.
st.markdown(
    """
    <style>
    [data-testid="stHeader"] { display: none; }
    [data-testid="stSidebar"] { display: none; }
    [data-testid="stAppViewContainer"] { background: #f3f7f8; }
    [data-testid="stMainBlockContainer"] {
        max-width: none;
        padding: 0;
    }
    iframe[title="streamlit.components.v1.html"] {
        display: block;
        border: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def load_dashboard(path: str, modified_time: float) -> str:
    """Load the dashboard and refresh the cache after the HTML changes."""
    del modified_time
    return Path(path).read_text(encoding="utf-8")


if not DASHBOARD_FILE.is_file():
    st.error(
        "Dashboard HTML was not found. Keep "
        "AI_Workforce_Investment_Planner.html in the same folder as streamlit_app.py."
    )
    st.stop()

dashboard_html = load_dashboard(
    str(DASHBOARD_FILE),
    DASHBOARD_FILE.stat().st_mtime,
)

# The component keeps all existing JavaScript interactions, maps, charts,
# table filters, and CSV downloads inside one desktop-sized viewport.
components.html(
    dashboard_html,
    height=1050,
    scrolling=True,
)

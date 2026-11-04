"""Streamlit entry point: streamlit run app.py"""
import streamlit as st
import streamlit.components.v1 as components

from generate_ai_workforce_planner import HTML_BYTES

st.set_page_config(
    page_title="AI Workforce Investment Planner",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

@st.cache_data(show_spinner=False)
def get_html():
    """Load the complete offline page, including its scripts and data."""
    return HTML_BYTES.decode("utf-8")

components.html(get_html(), height=1400, scrolling=True)

"""
Web应用模块 - 基于Streamlit的Web界面主入口。
"""

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="ResearchAgent", page_icon="O", layout="wide")

from src.web.session import get_agent
from src.web.views import home, dataset, assistant, meeting, paper, task, experiment, knowledge


def load_css():
    css_path = Path(__file__).parent / "static" / "style.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


PAGES = ["Home", "Assistant", "Dataset", "Meeting", "Paper", "Task", "Experiment", "Knowledge"]
VIEWS = {
    "Home": home, "Assistant": assistant, "Knowledge": knowledge,
    "Dataset": dataset, "Meeting": meeting, "Paper": paper,
    "Experiment": experiment, "Task": task,
}


def render_nav():
    st.sidebar.title("ResearchAgent")

    if "nav_page" not in st.session_state:
        st.session_state["nav_page"] = "Home"

    current = st.session_state["nav_page"]
    default_idx = PAGES.index(current) if current in PAGES else 0

    page = st.sidebar.radio(
        "Navigation",
        PAGES,
        index=default_idx,
        label_visibility="collapsed",
    )

    if page != st.session_state["nav_page"]:
        st.session_state["nav_page"] = page

    return st.session_state["nav_page"]


def main():
    load_css()
    agent = get_agent()
    page = render_nav()
    VIEWS.get(page, home).render(agent)


if __name__ == "__main__":
    main()

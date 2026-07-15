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


def main():
    load_css()
    agent = get_agent()

    st.sidebar.title("ResearchAgent")

    page = st.sidebar.radio(
        "Navigation",
        ["Home", "Assistant", "Dataset", "Meeting", "Paper", "Task", "Experiment", "Knowledge"],
        label_visibility="collapsed",
    )

    views = {
        "Home": home, "Assistant": assistant, "Knowledge": knowledge,
        "Dataset": dataset, "Meeting": meeting, "Paper": paper,
        "Experiment": experiment, "Task": task,
    }

    views.get(page, home).render(agent)


if __name__ == "__main__":
    main()

"""
Web应用模块 - 基于Streamlit的Web界面主入口。

配置页面布局、导航和全局样式。
"""

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="ResearchAgent", page_icon="O", layout="wide")

from src.web.session import get_agent
from src.web.views import home, dataset, assistant, meeting, paper, task, experiment, knowledge


def load_css():
    """加载自定义CSS样式表。"""
    css_path = Path(__file__).parent / "static" / "style.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_nav():
    """渲染侧边栏导航菜单。"""
    st.sidebar.title("ResearchAgent")
    page = st.sidebar.radio(
        "Navigation",
        ["Home", "Assistant", "Dataset", "Meeting", "Paper", "Task", "Experiment", "Knowledge"],
        label_visibility="collapsed",
    )
    return page


def main():
    """Streamlit应用主入口。"""
    load_css()
    agent = get_agent()

    page = render_nav()

    if page == "Home":
        home.render(agent)
    elif page == "Assistant":
        assistant.render(agent)
    elif page == "Dataset":
        dataset.render(agent)
    elif page == "Meeting":
        meeting.render(agent)
    elif page == "Paper":
        paper.render(agent)
    elif page == "Task":
        task.render(agent)
    elif page == "Experiment":
        experiment.render(agent)
    elif page == "Knowledge":
        knowledge.render(agent)


if __name__ == "__main__":
    main()

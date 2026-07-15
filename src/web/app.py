"""
Web应用模块 - 基于Streamlit的Web界面主入口。

SaaS Enterprise Analytics 风格 — Dark Navy 侧边栏 + Corporate Blue 主题。
"""

import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="ResearchAgent",
    page_icon="O",
    layout="wide",
    initial_sidebar_state="expanded",
)

from src.web.session import get_agent
from src.web.views import home, dataset, assistant, meeting, paper, task, experiment, knowledge


def load_css():
    """加载自定义CSS样式表。"""
    css_path = Path(__file__).parent / "static" / "style.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def on_nav_change():
    """导航切换回调 — 由st.radio的on_change触发，避免rerun竞态。"""
    st.session_state["nav_page"] = st.session_state["_nav_radio"]


def render_nav():
    """渲染Corporate Blue侧边栏导航。"""
    with st.sidebar:
        st.markdown("""
        <div class="ra-nav-header">
            <div class="ra-nav-brand">ResearchAgent</div>
            <div class="ra-nav-version">v0.2.0 &mdash; AI Research Assistant</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="ra-nav-section">Workspace</div>', unsafe_allow_html=True)

        if "nav_page" not in st.session_state:
            st.session_state["nav_page"] = "Home"

        labels = {
            "Home": "System Overview",
            "Assistant": "AI Assistant",
            "Knowledge": "Knowledge Base",
            "Dataset": "Dataset Manager",
            "Meeting": "Meeting Analysis",
            "Paper": "Paper Analysis",
            "Experiment": "Experiment Tracker",
            "Task": "Task Manager",
        }
        page_keys = list(labels.keys())

        current = st.session_state["nav_page"]
        default_idx = page_keys.index(current) if current in page_keys else 0

        st.radio(
            "Workspace",
            page_keys,
            index=default_idx,
            key="_nav_radio",
            label_visibility="collapsed",
            format_func=lambda x: labels[x],
            on_change=on_nav_change,
        )

        st.markdown("---")
        st.markdown("""
        <div style="padding: 1rem 1.5rem; font-size: 0.7rem; color: rgba(255,255,255,0.3);">
            ResearchAgent v0.2.0<br>
            DairySheepHR Project
        </div>
        """, unsafe_allow_html=True)

    return st.session_state["nav_page"]


def main():
    """Streamlit应用主入口。"""
    load_css()
    agent = get_agent()

    page = render_nav()

    views = {
        "Home": home,
        "Assistant": assistant,
        "Knowledge": knowledge,
        "Dataset": dataset,
        "Meeting": meeting,
        "Paper": paper,
        "Experiment": experiment,
        "Task": task,
    }

    view = views.get(page, home)
    view.render(agent)


if __name__ == "__main__":
    main()

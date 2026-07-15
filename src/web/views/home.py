"""
主页视图 - 系统仪表板页面（Corporate Blue风格）。

展示系统状态指标、快速操作入口和关键能力概览。
"""

import streamlit as st

from src.web.components.page_header import render_page_header
from src.web.components.stat_card import render_metric, render_metric_row


def render(agent):
    """渲染系统概览仪表板。

    Args:
        agent: ResearchAgent实例
    """
    render_page_header("System Overview", "ResearchAgent status and capability overview")

    # Row 1 — System Status
    st.markdown("### System Status")
    status_metrics = [
        {"label": "LLM Engine", "value": "Ready" if agent.llm_service else "Offline"},
        {"label": "Knowledge Base", "value": "Active" if agent.knowledge_service and agent.knowledge_service.available else "Inactive"},
        {"label": "Embedding", "value": "Online" if agent.embedding_service and agent.embedding_service.available else "Offline"},
        {"label": "ASR", "value": "Ready" if agent.asr_service and agent.asr_service.available else "Offline"},
        {"label": "Vision", "value": "Online" if agent.vision_service and agent.vision_service.available else "Offline"},
    ]
    render_metric_row(status_metrics)

    # Row 2 — Data Overview
    st.markdown("### Data Overview")
    col1, col2, col3 = st.columns(3)
    with col1:
        try:
            papers = agent.managers.get("paper", None)
            paper_count = len(papers.list_all()) if papers and hasattr(papers, 'list_all') else 0
        except Exception:
            paper_count = 0
        render_metric("Papers Indexed", str(paper_count))
    with col2:
        try:
            meetings = agent.managers.get("meeting", None)
            meeting_count = len(meetings.list_all()) if meetings and hasattr(meetings, 'list_all') else 0
        except Exception:
            meeting_count = 0
        render_metric("Meetings Recorded", str(meeting_count))
    with col3:
        try:
            experiments = agent.managers.get("experiment", None)
            exp_count = len(experiments.list_all()) if experiments and hasattr(experiments, 'list_all') else 0
        except Exception:
            exp_count = 0
        render_metric("Experiments Tracked", str(exp_count))

    st.markdown("---")

    # Quick Actions
    st.markdown("### Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("AI Assistant", key="qa_assistant", use_container_width=True):
            st.session_state["nav_page"] = "Assistant"
    with col2:
        if st.button("Knowledge Base", key="qa_knowledge", use_container_width=True):
            st.session_state["nav_page"] = "Knowledge"
    with col3:
        if st.button("Dataset Manager", key="qa_dataset", use_container_width=True):
            st.session_state["nav_page"] = "Dataset"
    with col4:
        if st.button("Experiment Tracker", key="qa_experiment", use_container_width=True):
            st.session_state["nav_page"] = "Experiment"

    # Agent Capabilities
    st.markdown("---")
    st.markdown("### Available Agents")
    try:
        coordinator = agent.coordinator
        available = coordinator.available_agents if coordinator else []
    except Exception:
        available = list(agent.managers.keys()) if agent.managers else []

    if available:
        cols = st.columns(len(available))
        for i, name in enumerate(available):
            with cols[i]:
                st.markdown(f"""
                <div class="ra-section ra-animate-in ra-stagger-{i+1}">
                    <div style="font-weight: 600; color: var(--color-primary);">{name.title()}</div>
                    <div style="font-size: 0.8rem; color: var(--color-dark-grey); margin-top: 0.25rem;">
                        {'Ready' if name in agent.managers else 'Unavailable'}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="ra-empty">No agents configured. Check your configuration.</div>', unsafe_allow_html=True)

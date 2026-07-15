"""
主页视图模块 - 系统仪表板页面。

展示系统状态、最近活动和快速操作入口。
"""

import streamlit as st

from src.web.components.page_header import render_page_header
from src.web.components.stat_card import render_metric_row


def render(agent):
    """渲染系统概览主页。

    Args:
        agent: ResearchAgent实例
    """
    render_page_header("System Overview", "ResearchAgent Status & Capabilities")

    # 系统状态指标
    metrics = [
        {"label": "LLM", "value": "Ready" if agent.llm_service else "Not Configured"},
        {"label": "Embedding", "value": "Ready" if agent.embedding_service and agent.embedding_service.available else "Not Available"},
        {"label": "Knowledge", "value": "Ready" if agent.knowledge_service and agent.knowledge_service.available else "Not Available"},
        {"label": "ASR", "value": "Ready" if agent.asr_service and agent.asr_service.available else "Not Available"},
        {"label": "Vision", "value": "Ready" if agent.vision_service and agent.vision_service.available else "Not Available"},
    ]

    render_metric_row(metrics)

    st.markdown("---")
    st.markdown("### Quick Actions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Assistant", key="qa_asst", use_container_width=True):
            st.session_state["nav_page"] = "Assistant"
            st.rerun()
    with col2:
        if st.button("Dataset Manager", key="qa_ds", use_container_width=True):
            st.session_state["nav_page"] = "Dataset"
            st.rerun()
    with col3:
        if st.button("Knowledge Base", key="qa_kb", use_container_width=True):
            st.session_state["nav_page"] = "Knowledge"
            st.rerun()

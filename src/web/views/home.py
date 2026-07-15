"""
主页视图模块 - 系统仪表板页面。

展示系统状态和各模块入口引导。
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
    st.info("Use the **sidebar navigation** on the left to access all modules: Assistant, Dataset, Knowledge Base, Meeting Analysis, Paper Analysis, Experiment Tracker, and Task Manager.")

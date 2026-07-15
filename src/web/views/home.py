"""
主页视图模块 - 系统仪表板页面。

展示系统状态和模块入口。
"""

import streamlit as st

from src.web.components.page_header import render_page_header
from src.web.components.stat_card import render_metric_row


def render(agent):
    """渲染系统概览主页。"""
    render_page_header("系统概览", "ResearchAgent 状态与能力总览")

    metrics = [
        {"label": "LLM", "value": "就绪" if agent.llm_service else "未配置"},
        {"label": "嵌入服务", "value": "就绪" if agent.embedding_service and agent.embedding_service.available else "不可用"},
        {"label": "知识库", "value": "就绪" if agent.knowledge_service and agent.knowledge_service.available else "不可用"},
        {"label": "语音识别", "value": "就绪" if agent.asr_service and agent.asr_service.available else "不可用"},
        {"label": "视觉分析", "value": "就绪" if agent.vision_service and agent.vision_service.available else "不可用"},
    ]

    render_metric_row(metrics)

    st.markdown("---")
    st.markdown("### 功能模块")
    st.info("使用左侧边栏导航切换到各功能模块：AI 助手、知识库、数据集管理、会议分析、论文分析、实验追踪、任务管理。")

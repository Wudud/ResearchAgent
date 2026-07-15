"""
助手视图模块 - AI 对话助手界面。
"""

import streamlit as st

from src.web.components import check_manager, render_page_header


def render(agent):
    """渲染AI助手页面。"""
    if not check_manager(agent, "assistant"):
        return

    render_page_header("AI 助手", "基于知识库增强的智能对话")

    mgr = agent.managers["assistant"]

    conv_id = st.selectbox(
        "选择对话",
        options=mgr.list_conversations() if hasattr(mgr, 'list_conversations') else [],
        format_func=lambda c: getattr(c, 'title', c) if hasattr(c, 'title') else str(c),
    ) if hasattr(mgr, 'list_conversations') else None

    user_input = st.chat_input("输入你的问题...")
    if user_input:
        st.chat_message("user").write(user_input)
        with st.spinner("思考中..."):
            try:
                response = mgr.send_message(conv_id, user_input) if conv_id else "请先选择或创建一个对话。"
                st.chat_message("assistant").write(response)
            except Exception as e:
                st.error(f"回复失败：{e}")

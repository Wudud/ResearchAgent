"""
知识库视图模块 - 知识库管理和检索界面。
"""

import streamlit as st

from src.web.components import check_manager, render_page_header


def render(agent):
    """渲染知识库管理页面。"""
    if not check_manager(agent, "knowledge"):
        return

    render_page_header("知识库", "文档索引与语义检索")

    ks = agent.knowledge_service
    if not ks or not ks.available:
        st.warning("知识库服务不可用，请检查嵌入服务配置。")
        return

    query = st.text_input("搜索知识库", placeholder="输入关键词...")
    if query:
        with st.spinner("检索中..."):
            result = ks.search(query, top_k=5)
            if result and result.get("results"):
                for r in result["results"]:
                    title = r.get("metadata", {}).get("title", "无标题")
                    with st.expander(title):
                        st.write(r.get("document", "")[:500])
            else:
                st.info("未找到相关结果。")

"""
论文视图模块 - 论文管理界面。
"""

import streamlit as st

from src.web.components import check_manager, render_page_header


def render(agent):
    """渲染论文管理页面。"""
    if not check_manager(agent, "paper"):
        return

    render_page_header("论文分析", "导入、分析和提取论文关键信息")

    mgr = agent.managers["paper"]

    uploaded = st.file_uploader("上传论文", type=["pdf", "txt", "docx"], key="pp_upload")
    if uploaded and st.button("导入分析"):
        with st.spinner("分析中..."):
            try:
                import tempfile
                from pathlib import Path
                suffix = Path(uploaded.name).suffix
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                    f.write(uploaded.read())
                    paper = mgr.process_paper(f.name)
                st.success(f"论文导入成功：{getattr(paper, 'title', uploaded.name)}")
                if hasattr(paper, 'summary') and paper.summary:
                    st.markdown("### 摘要")
                    st.write(paper.summary)
            except Exception as e:
                st.error(f"导入失败：{e}")

    st.markdown("---")
    st.caption("支持 PDF、DOCX、TXT 格式。论文导入后自动进入知识库索引。")

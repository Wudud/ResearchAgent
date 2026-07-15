"""
任务视图模块 - 任务管理界面。
"""

import streamlit as st

from src.web.components import check_manager, render_page_header, render_metric_row


def render(agent):
    """渲染任务管理页面。"""
    if not check_manager(agent, "task"):
        return

    render_page_header("任务管理", "追踪和管理科研待办任务")

    mgr = agent.managers["task"]

    with st.form("new_task"):
        content = st.text_input("任务内容")
        c1, c2 = st.columns(2)
        with c1:
            priority = st.selectbox("优先级", ["high", "medium", "low"])
        with c2:
            source = st.selectbox("来源", ["Meeting", "Paper", "Assistant", "Experiment", "Manual"])
        if st.form_submit_button("添加任务") and content:
            try:
                mgr.create_task(content=content, priority=priority, source=source)
                st.success("任务已添加")
                st.rerun()
            except Exception as e:
                st.error(f"添加失败：{e}")

    try:
        stats = mgr.get_stats()
        if stats:
            metrics = [
                {"label": "总计", "value": str(stats.get("total", 0))},
                {"label": "已完成", "value": str(stats.get("completed", 0))},
                {"label": "进行中", "value": str(stats.get("in_progress", 0))},
                {"label": "完成率", "value": stats.get("completion_rate", "0%")},
            ]
            render_metric_row(metrics)
    except Exception:
        pass

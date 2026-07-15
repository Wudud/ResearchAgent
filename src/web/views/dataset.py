"""
数据集视图模块 - 数据集管理界面。
"""

import streamlit as st

from src.web.components import check_manager, render_page_header, render_metric_row


def render(agent):
    """渲染数据集管理页面。"""
    if not check_manager(agent, "dataset"):
        return

    render_page_header("数据集管理", "扫描、分析和导出研究数据集")

    mgr = agent.managers["dataset"]

    root = st.text_input("数据集根目录", value="./workspace/datasets")
    if st.button("扫描数据集"):
        with st.spinner("正在扫描..."):
            try:
                inventory = mgr.scan_dataset(root)
                st.success(f"扫描完成：{inventory.total_files} 个文件")
                metrics = [
                    {"label": "总文件数", "value": str(inventory.total_files)},
                    {"label": "总大小", "value": f"{inventory.total_size_bytes / 1024 / 1024:.1f} MB"},
                ]
                render_metric_row(metrics)
            except Exception as e:
                st.error(f"扫描失败：{e}")

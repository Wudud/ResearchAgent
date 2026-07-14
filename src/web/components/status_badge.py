"""
状态徽章组件 - 显示状态的彩色标签组件。

支持自定义颜色映射和状态文本。
使用HTML/CSS渲染带颜色的状态标识。
"""

import streamlit as st


def render_badge(status: str) -> str:
    """渲染带颜色的状态徽章。

    Args:
        status: 状态文本

    Returns:
        str: HTML格式的徽章标记
    """
    colors = {
        "completed": "#28a745",
        "active": "#007bff",
        "pending": "#ffc107",
        "error": "#dc3545",
        "running": "#17a2b8",
        "failed": "#dc3545",
    }
    color = colors.get(status.lower(), "#6c757d")
    return f'<span style="background:{color};color:white;padding:2px 8px;border-radius:10px;font-size:0.8em">{status}</span>'

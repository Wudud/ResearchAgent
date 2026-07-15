"""
状态徽章组件 - Corporate Blue风格彩色状态标签。
"""

import streamlit as st


def render_badge(status: str) -> str:
    """渲染带颜色的状态徽章。

    Args:
        status: 状态文本

    Returns:
        str: HTML格式的徽章标记
    """
    label_map = {
        "completed": "Completed",
        "active": "Active",
        "pending": "Pending",
        "error": "Error",
        "running": "Running",
        "failed": "Failed",
    }
    display = label_map.get(status.lower(), status)
    return f'<span class="ra-badge {status.lower()}">{display}</span>'

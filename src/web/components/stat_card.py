"""
统计卡片组件 - 展示关键指标的卡片UI组件。

支持图标、数值和趋势指示的自定义展示。
可单独渲染或作为行内多个指标展示。
"""

import streamlit as st


def render_metric(label: str, value):
    """渲染单个指标卡片。

    Args:
        label: 指标标签
        value: 指标数值
    """
    html = (
        f'<div class="ra-metric">'
        f'<div class="ra-metric-label">{label}</div>'
        f'<div class="ra-metric-value">{value}</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_metric_row(metrics: list[dict]):
    """渲染水平排列的多个指标卡片。

    Args:
        metrics: 指标列表，每项为 {"label": str, "value": any}
    """
    n = len(metrics)
    if n == 0:
        return
    cols = st.columns(n)
    for i, m in enumerate(metrics):
        with cols[i]:
            render_metric(
                label=m.get("label", ""),
                value=m.get("value", ""),
            )


render_stat_card = render_metric
render_stat_row = render_metric_row

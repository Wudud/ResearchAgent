"""
统计卡片组件 - 展示关键指标的Glassmorphism卡片。

支持图标、数值和趋势指示的自定义展示。
"""

import streamlit as st


def render_metric(label: str, value, animate: bool = True):
    """渲染单个指标卡片（Glassmorphism风格）。

    Args:
        label: 指标标签
        value: 指标数值
        animate: 是否应用入场动画
    """
    anim_class = "ra-animate-in" if animate else ""
    html = (
        f'<div class="ra-metric {anim_class}">'
        f'<div class="ra-metric-label">{label}</div>'
        f'<div class="ra-metric-value">{value}</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_metric_row(metrics: list[dict]):
    """渲染水平排列的多个指标卡片（CSS Grid自适应）。

    Args:
        metrics: 指标列表，每项为 {"label": str, "value": any}
    """
    if not metrics:
        return
    cols = st.columns(len(metrics))
    for i, m in enumerate(metrics):
        with cols[i]:
            render_metric(
                label=m.get("label", ""),
                value=m.get("value", ""),
                animate=(i == 0),
            )


render_stat_card = render_metric
render_stat_row = render_metric_row

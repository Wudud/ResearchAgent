"""
页面头部组件 - 统一的Corporate Blue标题和描述组件。
"""

import streamlit as st


def render_page_header(title: str, description: str = None):
    """渲染页面标题和描述。

    Args:
        title: 页面标题
        description: 页面描述（可选）
    """
    desc_html = (
        f'<div class="ra-page-desc">{description}</div>' if description else ""
    )
    st.markdown(
        f'<div class="ra-page-header"><h1>{title}</h1>{desc_html}</div>',
        unsafe_allow_html=True,
    )

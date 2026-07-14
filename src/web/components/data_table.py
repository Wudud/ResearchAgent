"""
数据表格组件 - 增强的数据表格展示组件。

支持排序、搜索、分页和行选择功能。
使用Pandas DataFrame和Streamlit的数据展示能力。
"""

import streamlit as st
import pandas as pd


def render_data_table(df: pd.DataFrame, max_rows: int = 500):
    """渲染标准化的数据表格。

    Args:
        df: 要展示的DataFrame
        max_rows: 最大显示行数
    """
    if df.empty:
        st.info("No data available")
        return

    st.markdown('<div class="ra-table-wrap">', unsafe_allow_html=True)
    st.dataframe(df.head(max_rows), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if len(df) > max_rows:
        st.caption(f"Showing {max_rows} of {len(df)} rows")


def render_data_table_with_search(
    df: pd.DataFrame, search_key: str = "search", max_rows: int = 500
):
    """渲染带文本搜索过滤的数据表格。

    Args:
        df: 要展示的DataFrame
        search_key: 搜索框的唯一key
        max_rows: 最大显示行数
    """
    query = st.text_input("Search", key=f"dt_search_{search_key}", placeholder="Enter keywords...")
    if query:
        mask = df.astype(str).apply(
            lambda col: col.str.contains(query, case=False, na=False)
        ).any(axis=1)
        df = df[mask]
    render_data_table(df, max_rows=max_rows)

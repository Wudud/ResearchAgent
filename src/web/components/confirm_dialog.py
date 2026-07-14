"""
确认对话框组件 - 通用的操作确认UI组件。

支持自定义标题、消息和确认/取消操作。
使用Streamlit的session_state管理确认状态。
"""

import streamlit as st


def confirm_action(item_name: str, item_id, key_prefix: str = "confirm") -> bool:
    """显示确认对话框并返回用户确认结果。

    Args:
        item_name: 要操作的项目名称
        item_id: 项目ID
        key_prefix: Streamlit组件的key前缀

    Returns:
        bool: 用户确认返回True，否则False
    """
    key = f"{key_prefix}_{item_id}"
    if key not in st.session_state:
        st.session_state[key] = False

    if not st.session_state[key]:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.warning(f"Are you sure you want to delete '{item_name}'?")
        with col2:
            if st.button("Confirm", key=f"{key}_btn"):
                st.session_state[key] = True
                st.rerun()
        return False
    else:
        del st.session_state[key]
        return True

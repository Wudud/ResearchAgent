"""
确认对话框组件 - Corporate Blue风格操作确认UI。
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
        st.markdown(f"""
        <div class="ra-confirm">
            <strong>Confirm Deletion</strong><br>
            Are you sure you want to delete <em>{item_name}</em>? This action cannot be undone.
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([3, 1, 1])
        with col2:
            if st.button("Cancel", key=f"{key}_cancel"):
                st.session_state[key] = False
        with col3:
            if st.button("Delete", key=f"{key}_btn", type="primary"):
                st.session_state[key] = True
                st.rerun()
        return False
    else:
        del st.session_state[key]
        return True

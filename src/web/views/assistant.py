import time
from pathlib import Path

import streamlit as st

from src.web.components import check_manager, render_page_header

def _on_audio_upload():
    if st.session_state.get("audio_upload") is not None:
        st.session_state["_stashed_audio"] = st.session_state["audio_upload"]

def _on_file_upload():
    if st.session_state.get("file_upload") is not None:
        st.session_state["_stashed_file"] = st.session_state["file_upload"]

def render(agent):
    assistant_mgr = check_manager(agent, "assistant")
    if assistant_mgr is None:
        return

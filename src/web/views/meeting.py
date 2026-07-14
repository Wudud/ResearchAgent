import time
from pathlib import Path

import streamlit as st

from src.web.components import check_manager, render_page_header, confirm_action

def render(agent):
    meeting_mgr = check_manager(agent, "meeting")
    if meeting_mgr is None:
        return

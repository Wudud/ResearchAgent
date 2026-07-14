from pathlib import Path

import streamlit as st

from src.web.components import check_manager, render_page_header, confirm_action

def render(agent):
    paper_mgr = check_manager(agent, "paper")
    if paper_mgr is None:
        return

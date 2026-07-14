import streamlit as st

from src.web.components import check_manager, render_page_header, render_metric_row

def render(agent):
    knowledge_mgr = check_manager(agent, "knowledge")
    if knowledge_mgr is None:
        return

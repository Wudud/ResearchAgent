import streamlit as st

from src.web.components import check_manager, render_page_header, render_metric_row

def render(agent):
    task_mgr = check_manager(agent, "task")
    if task_mgr is None:
        return

from pathlib import Path

import streamlit as st
import pandas as pd

from src.web.components import check_manager, render_page_header, render_data_table, render_metric_row

def render(agent):
    dataset_mgr = check_manager(agent, "dataset")
    if dataset_mgr is None:
        return

import json

import streamlit as st
import pandas as pd

from src.web.components import check_manager, render_page_header, render_badge, confirm_action

def render(agent):
    exp_mgr = check_manager(agent, "experiment")
    if exp_mgr is None:
        return

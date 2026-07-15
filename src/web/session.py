import streamlit as st

from src.core.agent import ResearchAgent

@st.cache_resource
def get_agent() -> ResearchAgent:
    agent = ResearchAgent()
    agent.initialize()
    return agent

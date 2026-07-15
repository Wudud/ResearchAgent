"""
会议视图模块 - 会议管理界面。
"""

import streamlit as st

from src.web.components import check_manager, render_page_header


def render(agent):
    """渲染会议管理页面。"""
    if not check_manager(agent, "meeting"):
        return

    render_page_header("会议分析", "转录、分析和提取会议要点")

    mgr = agent.managers["meeting"]
    tab1, tab2 = st.tabs(["文本输入", "音频上传"])

    with tab1:
        title = st.text_input("会议标题", key="mt_title")
        text = st.text_area("会议内容", height=200, placeholder="粘贴会议文本...")
        if st.button("分析文本") and text:
            with st.spinner("分析中..."):
                try:
                    meeting = mgr.process_meeting_text(text, title)
                    st.success("分析完成")
                    if hasattr(meeting, 'summary') and meeting.summary:
                        st.markdown("### 摘要")
                        st.write(meeting.summary)
                except Exception as e:
                    st.error(f"分析失败：{e}")

    with tab2:
        audio = st.file_uploader("上传音频", type=["wav", "mp3", "m4a"], key="mt_audio")
        if audio and st.button("转录音频"):
            with st.spinner("转录中..."):
                try:
                    import tempfile
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio.name.split('.')[-1]}") as f:
                        f.write(audio.read())
                        meeting = mgr.transcribe_meeting(f.name, title or audio.name)
                        st.success("转录完成")
                except Exception as e:
                    st.error(f"转录失败：{e}")

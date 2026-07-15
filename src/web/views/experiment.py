"""
实验视图模块 - 实验管理界面。
"""

import streamlit as st

from src.web.components import check_manager, render_page_header, render_metric_row


def render(agent):
    """渲染实验管理页面。"""
    if not check_manager(agent, "experiment"):
        return

    render_page_header("实验追踪", "创建、监控和对比机器学习实验")

    mgr = agent.managers["experiment"]
    service = mgr._service if hasattr(mgr, '_service') else None

    with st.form("new_experiment"):
        st.markdown("### 新建实验")
        name = st.text_input("实验名称")
        c1, c2 = st.columns(2)
        with c1:
            dataset = st.text_input("数据集")
        with c2:
            model = st.text_input("模型")
        params_str = st.text_input("参数 (JSON)", value='{"lr": 0.001}')
        if st.form_submit_button("创建实验") and name:
            try:
                params = __import__('json').loads(params_str)
                exp = service.create_experiment(name=name, dataset=dataset, model=model, parameters=params)
                st.success(f"实验创建成功：ID={exp.id}")
            except Exception as e:
                st.error(f"创建失败：{e}")

    st.markdown("---")
    if service:
        try:
            exps = service.list_experiments()
            if exps:
                st.markdown(f"### 实验列表（共 {len(exps)} 个）")
                for e in exps[:10]:
                    st.markdown(f"- **[{e.id}]** {e.name} — {getattr(e, 'status', 'N/A')}")
        except Exception:
            pass

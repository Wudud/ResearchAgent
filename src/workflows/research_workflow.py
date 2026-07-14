"""
研究工作流模块 - 论文、会议、实验和数据集的标准研究流程。

每个工作流定义了从数据输入到报告生成的标准处理步骤。
"""

from src.workflows.base_workflow import BaseWorkflow


class PaperWorkflow(BaseWorkflow):
    """论文处理流程：读取→分析→索引→提取任务。"""

    def run(self, file_path: str, auto_index: bool = True) -> dict:
        """执行论文处理工作流。

        Args:
            file_path: 论文文件路径
            auto_index: 是否自动索引到知识库

        Returns:
            dict: 处理结果
        """
        paper_mgr = self.agent.managers.get("paper")
        knowledge_mgr = self.agent.managers.get("knowledge")
        task_mgr = self.agent.managers.get("task")

        if paper_mgr is None:
            return {"status": "error", "message": "Paper Manager not available"}

        paper = paper_mgr.process_paper(file_path)

        if auto_index and knowledge_mgr and paper:
            knowledge_mgr.index_paper(paper)

        if task_mgr and paper:
            task_mgr.create_task(
                content=f"Review paper: {getattr(paper, 'title', file_path)}",
                source="Paper",
                priority="medium",
            )

        return {"status": "completed", "paper": paper}


class MeetingWorkflow(BaseWorkflow):
    """会议分析流程：转录/处理→分析→索引→提取任务。"""

    def run(self, audio_path: str = None, text: str = None, title: str = None, auto_index: bool = True) -> dict:
        """执行会议分析工作流。

        Args:
            audio_path: 会议音频文件路径
            text: 会议文本内容
            title: 会议标题
            auto_index: 是否自动索引到知识库

        Returns:
            dict: 处理结果
        """
        meeting_mgr = self.agent.managers.get("meeting")
        knowledge_mgr = self.agent.managers.get("knowledge")
        task_mgr = self.agent.managers.get("task")

        if meeting_mgr is None:
            return {"status": "error", "message": "Meeting Manager not available"}

        if audio_path:
            meeting = meeting_mgr.transcribe_meeting(audio_path, title)
        elif text:
            meeting = meeting_mgr.process_meeting_text(text, title)
        else:
            return {"status": "error", "message": "Either audio_path or text is required"}

        if auto_index and knowledge_mgr and meeting:
            knowledge_mgr.index_meeting(meeting)

        if task_mgr and meeting:
            task_mgr.create_tasks_batch(
                getattr(meeting, '_tasks', []), source="Meeting"
            )

        return {"status": "completed", "meeting": meeting}


class ExperimentWorkflow(BaseWorkflow):
    """实验流程：创建→记录指标→生成报告→索引。"""

    def run(self, name: str, dataset: str = "", model: str = "", parameters: dict = None,
            metrics: list[dict] = None, auto_index: bool = True) -> dict:
        """执行实验管理工作流。

        Args:
            name: 实验名称
            dataset: 数据集名称
            model: 模型名称
            parameters: 参数字典
            metrics: 指标列表
            auto_index: 是否自动索引

        Returns:
            dict: 处理结果
        """
        exp_mgr = self.agent.managers.get("experiment")
        knowledge_mgr = self.agent.managers.get("knowledge")

        if exp_mgr is None:
            return {"status": "error", "message": "Experiment Manager not available"}

        exp = exp_mgr.create_experiment(
            name=name, dataset=dataset, model=model, parameters=parameters,
        )

        if metrics:
            for m in metrics:
                step = m.pop("step", None)
                exp_mgr.log_metrics(exp.id, step=step, **m)

        report = exp_mgr.generate_report(exp.id) if hasattr(exp_mgr, 'generate_report') else ""

        if auto_index and knowledge_mgr and exp:
            knowledge_mgr.index_experiment(exp)

        return {"status": "completed", "experiment": exp, "report": report}


class DatasetWorkflow(BaseWorkflow):
    """数据集流程：扫描→完整性→统计→报告→卡片→索引。"""

    def run(self, root_path: str = None, dataset_name: str = None, auto_index: bool = True) -> dict:
        """执行数据集分析工作流。

        Args:
            root_path: 数据集根目录
            dataset_name: 数据集名称
            auto_index: 是否自动索引

        Returns:
            dict: 处理结果
        """
        dataset_mgr = self.agent.managers.get("dataset")
        knowledge_mgr = self.agent.managers.get("knowledge")

        if dataset_mgr is None:
            return {"status": "error", "message": "Dataset Manager not available"}

        inventory = dataset_mgr.scan_dataset(root_path)
        integrity = dataset_mgr.check_integrity()
        stats = dataset_mgr.get_statistics()
        report = dataset_mgr.generate_report(dataset_name)
        card = dataset_mgr.generate_dataset_card(dataset_name)

        if auto_index and knowledge_mgr:
            knowledge_mgr.index_dataset_info(dataset_name or "Dataset", report)

        return {
            "status": "completed",
            "inventory": inventory,
            "integrity": integrity,
            "stats": stats,
            "report": report,
            "card": card,
        }

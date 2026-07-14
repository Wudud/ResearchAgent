from src.workflows.base_workflow import BaseWorkflow

class AutoIndexWorkflow(BaseWorkflow):
    """Batch index all papers, meetings, and experiments into knowledge base."""

    def run(self) -> dict:
        knowledge_mgr = self.agent.managers.get("knowledge")

        if knowledge_mgr is None:
            return {"status": "error", "message": "Knowledge Manager not available"}

        results = {"papers": 0, "meetings": 0, "experiments": 0}

        paper_mgr = self.agent.managers.get("paper")
        if paper_mgr:
            for p in paper_mgr.list_papers():
                results["papers"] += knowledge_mgr.index_paper(p)

        meeting_mgr = self.agent.managers.get("meeting")
        if meeting_mgr:
            for m in meeting_mgr.list_meetings():
                results["meetings"] += knowledge_mgr.index_meeting(m)

        exp_mgr = self.agent.managers.get("experiment")
        if exp_mgr:
            for exp in exp_mgr.list_experiments():
                results["experiments"] += knowledge_mgr.index_experiment(exp)

        total = sum(results.values())
        return {"status": "completed", "indexed": results, "total": total}

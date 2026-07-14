from unittest.mock import MagicMock

import pytest

from src.mcp.registry import ToolRegistry
from src.mcp.tools import register_all

class TestToolRegistry:
    @pytest.fixture
    def registry(self):
        r = ToolRegistry()
        r.register("test_tool", "A test tool",
                   {"type": "object", "properties": {"x": {"type": "integer"}}, "required": ["x"]},
                   lambda agent, args: {"result": args["x"] * 2})
        return r

    def test_list_tools(self, registry):
        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "test_tool"
        assert "inputSchema" in tools[0]

    def test_execute_success(self, registry):
        mock_agent = MagicMock()
        result = registry.execute("test_tool", {"x": 5}, mock_agent)
        assert "content" in result
        assert "10" in result["content"][0]["text"]

    def test_execute_unknown_tool(self, registry):
        result = registry.execute("nonexistent", {}, MagicMock())
        assert "error" in result

    def test_tool_names(self, registry):
        assert "test_tool" in registry.tool_names

class TestMCPToolRegistration:
    @pytest.fixture
    def registry(self):
        r = ToolRegistry()
        register_all(r)
        return r

    def test_all_tools_registered(self, registry):
        # Should have all 23 tools across 8 categories
        names = registry.tool_names
        assert len(names) >= 20
        # Spot-check key tools exist
        for expected in ["paper_process", "meeting_list", "experiment_create",
                         "task_list", "knowledge_search", "dataset_scan",
                         "research_memory_query", "assistant_chat"]:
            assert expected in names, f"Missing tool: {expected}"

    def test_all_tools_have_schemas(self, registry):
        tools = registry.list_tools()
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert "type" in tool["inputSchema"]

    def test_no_duplicate_names(self, registry):
        names = registry.tool_names
        assert len(names) == len(set(names))

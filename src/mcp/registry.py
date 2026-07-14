

class ToolRegistry:
    """MCP工具注册表 - 管理工具的生命周期。

    """

    def __init__(self):
        self._tools = {}

    def register(self, name: str, description: str, input_schema: dict, handler):
        """Register a tool. handler receives (agent, arguments) and returns a dict."""
        self._tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
            "handler": handler,
        }

    def list_tools(self) -> list[dict]:
        """Return MCP-compliant tool list."""
        return [
            {"name": t["name"], "description": t["description"], "inputSchema": t["inputSchema"]}
            for t in self._tools.values()
        ]

    def execute(self, name: str, arguments: dict, agent) -> dict:
        """Dispatch a tool call. Returns {"content": [...]} or {"error": "..."}."""
        tool = self._tools.get(name)
        if tool is None:
            return {"error": f"Unknown tool: {name}"}
        try:
            result = tool["handler"](agent, arguments)
            return {"content": [{"type": "text", "text": str(result)}]}
        except Exception as e:
            return {"error": str(e)}

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools.keys())

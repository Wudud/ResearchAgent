"""
MCP服务器模块 - 基于stdio的Model Context Protocol服务器。

将ResearchAgent功能暴露为MCP工具供外部客户端调用。
使用JSON-RPC协议在stdin/stdout上通信。
"""

import json
import sys
import traceback

from src.mcp.registry import ToolRegistry
from src.mcp.tools import register_all


def run_mcp_server(agent):
    """运行MCP stdio服务器主循环。

    从stdin读取JSON-RPC请求，处理后写入stdout。
    支持initialize、tools/list、tools/call和shutdown方法。

    Args:
        agent: ResearchAgent实例
    """
    registry = ToolRegistry()
    register_all(registry)

    agent.logger.info(f"MCP server starting with {len(registry.tool_names)} tools: {registry.tool_names}")

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            _write_error(None, "Invalid JSON")
            continue

        method = request.get("method", "")
        req_id = request.get("id")

        if method == "initialize":
            _write_result(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "ResearchAgent", "version": "0.2.0"},
            })

        elif method == "tools/list":
            _write_result(req_id, {"tools": registry.list_tools()})

        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = registry.execute(tool_name, arguments, agent)
            _write_result(req_id, result)

        elif method == "shutdown":
            _write_result(req_id, {})
            agent.logger.info("MCP server shutting down")
            sys.exit(0)

        elif method == "notifications/initialized":
            pass

        else:
            _write_error(req_id, f"Unknown method: {method}")


def _write_result(req_id, result):
    """写入JSON-RPC成功响应到stdout。

    Args:
        req_id: 请求ID
        result: 响应结果
    """
    _write({"jsonrpc": "2.0", "id": req_id, "result": result})


def _write_error(req_id, message):
    """写入JSON-RPC错误响应到stdout。

    Args:
        req_id: 请求ID
        message: 错误消息
    """
    _write({"jsonrpc": "2.0", "id": req_id, "error": {"code": -1, "message": message}})


def _write(data):
    """写入JSON-RPC消息到stdout并立即刷新。

    Args:
        data: 要序列化为JSON的数据字典
    """
    sys.stdout.write(json.dumps(data, ensure_ascii=False) + "\n")
    sys.stdout.flush()

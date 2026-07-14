"""
自定义异常模块 - 定义ResearchAgent系统中所有异常类型

所有异常继承自ResearchAgentError基类，便于统一捕获和处理。
各子类异常对应不同的故障域，便于定位问题来源。
"""


class ResearchAgentError(Exception):
    """所有ResearchAgent异常的基类。"""
    pass


class ConfigError(ResearchAgentError):
    """配置异常 - 配置文件缺失、格式错误或必需环境变量未设置。"""
    pass


class LLMError(ResearchAgentError):
    """LLM异常 - API调用失败（网络错误、认证失败、速率限制等）。"""
    pass


class ToolError(ResearchAgentError):
    """工具异常 - 工具执行失败（文件未找到、解析错误等）。"""
    pass


class ManagerError(ResearchAgentError):
    """管理器异常 - 管理器级别错误（无效状态、缺少依赖等）。"""
    pass


class ASRError(ResearchAgentError):
    """语音识别异常 - 模型加载失败、音频格式不支持等。"""
    pass


class ChatError(ResearchAgentError):
    """对话异常 - 对话级别错误（无效对话ID等）。"""
    pass


class MCPError(ResearchAgentError):
    """MCP协议异常 - 工具调用无效、序列化失败等。"""
    pass


class AgentError(ResearchAgentError):
    """Agent执行异常 - ReAct循环失败、工具未找到、超时等。"""
    pass


class PlanningError(ResearchAgentError):
    """研究规划异常 - LLM返回无效的规划JSON等。"""
    pass


class HealthCheckError(ResearchAgentError):
    """健康检查异常 - 检查器自身故障（非被检查组件故障）。"""
    pass

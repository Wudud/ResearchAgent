"""
日志配置模块 - 统一的日志系统配置

支持控制台和文件双通道输出，文件日志使用RotatingFileHandler自动轮转。
使用ContextVar存储请求ID，支持在并发/异步操作中追踪关联的日志条目。
"""

import logging
import os
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 线程安全的请求ID，用于在并发操作中追踪关联的日志条目。
# MCP服务器和异步工作流使用此变量关联日志记录。
request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """获取当前请求ID，未设置时返回空字符串。

    Returns:
        str: 当前的请求ID
    """
    return request_id_var.get()


def setup_logging(config) -> logging.Logger:
    """配置日志系统并返回根日志器。

    配置包括：
    - 日志级别（从配置文件读取）
    - 文件输出（按大小自动轮转）
    - 控制台输出
    - 统一的格式化器

    Args:
        config: ConfigManager实例

    Returns:
        logging.Logger: 配置好的ResearchAgent日志器
    """
    level = config.get("logging.level", "INFO")
    log_dir = config.get("logging.log_dir", "./logs")
    max_bytes = config.get("logging.max_bytes_per_file", 10 * 1024 * 1024)
    backup_count = config.get("logging.backup_count", 3)

    # 确保日志目录存在
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("ResearchAgent")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 文件处理器 - 按大小自动轮转
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "research_agent.log"),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialized — level={level}, dir={log_dir}")
    return logger

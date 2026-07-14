"""
配置管理模块 - YAML配置文件的加载、解析和验证

支持通过点号路径访问嵌套配置项，并能自动解析${ENV_VAR}环境变量占位符。
"""

import os
import re
from pathlib import Path

import yaml

from src.utils.exceptions import ConfigError


class ConfigManager:
    """配置管理器 - 负责加载、验证和访问YAML配置文件。

    支持功能：
    - 按点号分隔的路径访问嵌套配置（如 "llm.providers.openai.api_key"）
    - 自动解析${环境变量}占位符
    - 配置完整性验证

    Attributes:
        _config_path: 配置文件的绝对路径
        _data: 解析后的配置字典
    """

    def __init__(self, config_path: str = None):
        """初始化配置管理器。

        Args:
            config_path: YAML配置文件路径，为None时使用默认配置文件

        Raises:
            ConfigError: 配置文件不存在时抛出
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "configs" / "default.yaml"

        self._config_path = Path(config_path)
        if not self._config_path.exists():
            raise ConfigError(f"Config file not found: {self._config_path}")

        self._data = self._load()

    def _load(self) -> dict:
        """加载并解析YAML配置文件。

        先读取原始文本并解析环境变量占位符，再通过yaml.safe_load解析。

        Returns:
            dict: 解析后的配置字典

        Raises:
            ConfigError: YAML格式错误时抛出
        """
        with open(self._config_path, "r", encoding="utf-8") as f:
            raw = f.read()

        # 解析 ${ENV_VAR} 环境变量占位符
        raw = self._resolve_env_vars(raw)

        try:
            return yaml.safe_load(raw)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML in config file: {self._config_path}") from e

    def _resolve_env_vars(self, raw: str) -> str:
        """将YAML文本中的${ENV_VAR}占位符替换为实际环境变量值。

        Args:
            raw: 包含占位符的原始YAML文本

        Returns:
            str: 替换后的YAML文本

        Raises:
            ConfigError: 引用的环境变量未设置时抛出
        """
        pattern = re.compile(r"\$\{(\w+)\}")

        def replacer(match):
            var_name = match.group(1)
            value = os.environ.get(var_name)
            if value is None:
                raise ConfigError(
                    f"Environment variable '{var_name}' is not set, "
                    f"required by config: {self._config_path}"
                )
            return value

        return pattern.sub(replacer, raw)

    def get(self, key_path: str, default=None):
        """通过点号分隔的路径获取配置值。

        Args:
            key_path: 点号分隔的配置路径，如 "llm.default_provider"
            default: 路径不存在时返回的默认值

        Returns:
            对应路径的配置值，路径不存在时返回default
        """
        keys = key_path.split(".")
        node = self._data

        for key in keys:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                return default

        return node

    def validate(self) -> list[str]:
        """验证配置完整性，返回警告信息列表。

        检查内容包括：
        - 必需的顶层配置段（agent、logging）是否存在
        - 工作空间目录是否存在
        - LLM默认provider是否有对应配置

        注意：只对可选的/缺失的配置发出警告，真正损坏的状态会抛出ConfigError。

        Returns:
            list[str]: 配置警告信息列表
        """
        warnings = []

        # 检查必需的顶层配置段
        for section in ["agent", "logging"]:
            if section not in self._data:
                warnings.append(f"Missing config section: '{section}'")

        # 检查工作空间路径
        ws = self.get("agent.workspace_dir", "./workspace")
        if ws:
            p = Path(ws)
            if not p.exists():
                warnings.append(f"Workspace directory does not exist: {ws}")

        # 检查LLM配置一致性
        default_provider = self.get("llm.default_provider")
        if default_provider:
            provider_config = self.get(f"llm.providers.{default_provider}")
            if provider_config is None:
                warnings.append(f"LLM default_provider '{default_provider}' has no config")

        return warnings

    @property
    def data(self) -> dict:
        """返回完整的配置数据字典。

        Returns:
            dict: 所有配置项的字典
        """
        return self._data

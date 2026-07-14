"""
核心Agent模块 - ResearchAgent主类

ResearchAgent是整个系统的核心编排器，负责初始化和管理所有服务、工具和管理器。
它作为依赖注入容器，将各组件连接在一起，提供统一的服务访问入口。
"""

from src.config.config_manager import ConfigManager
from src.utils.logging_config import setup_logging
from src.utils.exceptions import ConfigError
from src.llm.adapter_factory import create_llm_adapter
from src.asr.adapter_factory import create_asr_adapter
from src.embedding.adapter_factory import create_embedding_adapter
from src.services.llm_service import LLMService
from src.services.embedding_service import EmbeddingService
from src.services.prompt_service import PromptService
from src.services.memory_service import MemoryService
from src.services.asr_service import ASRService
from src.services.research_memory_service import ResearchMemoryService
from src.services.report_service import ReportService
from src.services.knowledge_service import KnowledgeService
from src.persistence.conversation_repository import ConversationRepository
from src.persistence.meeting_repository import MeetingRepository
from src.persistence.paper_repository import PaperRepository
from src.persistence.task_repository import TaskRepository
from src.persistence.memory_repository import ResearchMemoryRepository
from src.persistence.experiment_repository import ExperimentRepository
from src.tools.filesystem.scanner import FileScanner
from src.tools.filesystem.checksum import ChecksumTool
from src.tools.pointcloud.ply_reader import PLYReader
from src.tools.pointcloud.pcd_reader import PCDReader
from src.tools.pointcloud.statistics import PointCloudStatistics
from src.managers.dataset_manager import DatasetManager
from src.managers.assistant_manager import AssistantManager
from src.managers.meeting_manager import MeetingManager
from src.managers.paper_manager import PaperManager
from src.managers.task_manager import TaskManager
from src.managers.experiment_manager import ExperimentManager
from src.managers.knowledge_manager import KnowledgeManager
from src.workflows.research_workflow import PaperWorkflow, MeetingWorkflow, ExperimentWorkflow, DatasetWorkflow
from src.workflows.auto_index_workflow import AutoIndexWorkflow


class ResearchAgent:
    """ResearchAgent主类 - 系统的核心编排器和依赖注入容器。

    负责初始化和管理所有子系统组件，包括：
    - LLM、ASR、视觉、嵌入等服务
    - 知识库和语义记忆
    - 数据库仓库（对话、会议、论文、任务等）
    - 工具集（文件扫描、点云处理等）
    - 管理器（数据集、助手、会议、论文等）
    - 工作流（论文、会议、实验、数据集、自动索引）

    Attributes:
        config: 配置管理器实例
        logger: 日志记录器
        llm_service: 大语言模型服务
        asr_service: 语音识别服务
        vision_service: 视觉分析服务
        embedding_service: 嵌入向量服务
        knowledge_service: 知识库服务
        services: 所有服务的字典集合
        tools: 所有工具的字典集合
        managers: 所有管理器的字典集合
        workflows: 所有工作流的字典集合
    """

    def __init__(self, config_path: str = None):
        """初始化ResearchAgent及其所有子系统组件。

        Args:
            config_path: YAML配置文件路径，为None时使用默认配置

        Raises:
            ConfigError: 配置文件不存在或格式错误时抛出
        """
        # 加载配置
        self.config = ConfigManager(config_path)

        # 初始化日志系统
        self.logger = setup_logging(self.config)

        # LLM服务 - 大语言模型接口
        try:
            llm_adapter = create_llm_adapter(self.config)
            self.llm_service = LLMService(llm_adapter)
            self.logger.info(f"LLM provider: {self.llm_service.provider}")
        except (ConfigError, ValueError) as e:
            self.logger.warning(f"LLM not configured: {e}")
            self.llm_service = None

        # ASR服务 - 语音识别
        try:
            asr_adapter = create_asr_adapter(self.config)
            self.asr_service = ASRService(asr_adapter)
            self.logger.info(f"ASR provider: {self.asr_service.provider}")
        except (ConfigError, ValueError) as e:
            self.logger.warning(f"ASR not configured: {e}")
            self.asr_service = ASRService(None)

        # 视觉服务 - 图像分析和理解
        from src.vision.adapter_factory import create_vision_adapter
        from src.vision.vision_service import VisionService
        try:
            vision_adapter = create_vision_adapter(self.config)
            self.vision_service = VisionService(vision_adapter)
            self.logger.info(f"Vision provider: {self.vision_service.provider}")
        except (ConfigError, ValueError) as e:
            self.logger.warning(f"Vision not configured: {e}")
            self.vision_service = VisionService(None)

        # 嵌入服务 - 文本向量化
        try:
            embedding_adapter = create_embedding_adapter(self.config)
            self.embedding_service = EmbeddingService(embedding_adapter)
            self.logger.info(f"Embedding provider: {self.embedding_service.provider}")
        except (ConfigError, ValueError) as e:
            self.logger.warning(f"Embedding not configured: {e}")
            self.embedding_service = EmbeddingService(None)

        # 知识库服务 - 文档索引与检索
        from src.knowledge.reranker import Reranker
        knowledge_persist_dir = self.config.get("knowledge.persist_dir", "./workspace/chroma_db")
        reranker_model = self.config.get("knowledge.reranker_model", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        reranker = Reranker(model_name=reranker_model)
        self.logger.info(f"Reranker available: {reranker.available}")

        self.knowledge_service = KnowledgeService(
            embedding_service=self.embedding_service,
            persist_dir=knowledge_persist_dir,
            reranker=reranker,
        )
        self.logger.info(f"Knowledge service ready: {self.knowledge_service.available}")

        # 初始化缓存层
        self._init_caches()

        # 数据库仓库 - 持久化存储
        db_path = self.config.get("chat.db_path", "./workspace/chat_history.db")
        self.conversation_repo = ConversationRepository(db_path)
        self.meeting_repo = MeetingRepository(db_path)
        self.paper_repo = PaperRepository(db_path)
        self.task_repo = TaskRepository(db_path)
        self.research_memory_repo = ResearchMemoryRepository(db_path)
        self.experiment_repo = ExperimentRepository(db_path)

        # 语义记忆存储 - 基于向量相似度的记忆系统
        from src.memory.semantic_store import SemanticMemoryStore
        self.semantic_store = SemanticMemoryStore(
            embedding_service=self.embedding_service,
            persist_dir=knowledge_persist_dir,
        )

        # 服务注册表 - 统一管理所有服务实例
        self.services = {
            "llm": self.llm_service,
            "prompt": PromptService(),
            "memory": MemoryService(semantic_store=self.semantic_store),
            "asr": self.asr_service,
            "conversation_repo": self.conversation_repo,
            "meeting_repo": self.meeting_repo,
            "paper_repo": self.paper_repo,
            "task_repo": self.task_repo,
            "research_memory_repo": self.research_memory_repo,
            "experiment_repo": self.experiment_repo,
            "research_memory": ResearchMemoryService(self.research_memory_repo, semantic_store=self.semantic_store),
            "report": ReportService(self.llm_service, PromptService()),
            "embedding": self.embedding_service,
            "vision": self.vision_service,
            "knowledge_service": self.knowledge_service,
        }

        # 工具注册表 - 文件处理和分析工具
        self.tools = {
            "file_scanner": FileScanner(),
            "checksum": ChecksumTool(),
            "ply_reader": PLYReader(),
            "pcd_reader": PCDReader(),
            "pointcloud_statistics": PointCloudStatistics(),
        }

        # 管理器注册表 - 业务逻辑管理器
        self.managers = {}
        self._register_managers()

    def _init_caches(self):
        """初始化缓存系统。

        根据配置决定是否启用三种缓存：
        - EmbeddingCache: 文本→嵌入向量的LRU缓存
        - LLMResponseCache: LLM对话响应的TTL缓存
        - ChromaCollectionCache: ChromaDB集合句柄缓存
        """
        from src.utils.cache import EmbeddingCache, LLMResponseCache, ChromaCollectionCache

        enable_embedding = self.config.get("cache.embedding", False)
        enable_llm = self.config.get("cache.llm", False)
        enable_chroma = self.config.get("cache.chroma", False)

        if enable_embedding and self.embedding_service:
            self.embedding_service._cache = EmbeddingCache()
            self.logger.info("Embedding cache enabled")

        if enable_llm and self.llm_service:
            self.llm_service._cache = LLMResponseCache()
            self.logger.info("LLM response cache enabled")

        if enable_chroma and self.knowledge_service:
            cc = ChromaCollectionCache()
            self.knowledge_service._indexer._cache = cc
            self.knowledge_service._retriever._cache = cc
            self.logger.info("Chroma collection cache enabled")

    def _register_managers(self):
        """注册所有业务管理器、工作流和事件监听器。

        初始化7个管理器（数据集、助手、会议、论文、任务、实验、知识库），
        5个工作流，以及知识库事件监听器。
        """
        self.managers["dataset"] = DatasetManager(agent=self)
        self.managers["assistant"] = AssistantManager(agent=self)
        self.managers["meeting"] = MeetingManager(agent=self)
        self.managers["paper"] = PaperManager(agent=self)
        self.managers["task"] = TaskManager(agent=self)
        self.managers["experiment"] = ExperimentManager(agent=self)
        self.managers["knowledge"] = KnowledgeManager(agent=self)

        # 工作流注册
        self.workflows = {
            "paper": PaperWorkflow("Paper Workflow", agent=self),
            "meeting": MeetingWorkflow("Meeting Workflow", agent=self),
            "experiment": ExperimentWorkflow("Experiment Workflow", agent=self),
            "dataset": DatasetWorkflow("Dataset Workflow", agent=self),
            "auto_index": AutoIndexWorkflow("Auto Index Workflow", agent=self),
        }

        # 注册EventBus事件监听器
        from src.events.event_bus import EventBus
        from src.events.listeners import register_knowledge_listeners
        register_knowledge_listeners(EventBus(), self.managers.get("knowledge"))

    def initialize(self, quiet: bool = False):
        """初始化所有管理器并打印系统就绪信息。

        Args:
            quiet: 静默模式。MCP服务器模式下设为True，
                   因为stdio是JSON-RPC通道，任何额外输出都会破坏协议。
        """
        if not quiet:
            print("=" * 45)
            print(f"        ResearchAgent v{self.config.get('agent.version', '0.1.0')}")
            print("=" * 45)

        for name, mgr in self.managers.items():
            mgr.initialize()

        self.logger.info("ResearchAgent initialized.")
        if not quiet:
            print("\nSystem Ready.")

    @property
    def coordinator(self):
        """懒加载的AgentCoordinator - 仅在需要多Agent协作时创建。

        Returns:
            AgentCoordinator: 多Agent协调器实例
        """
        if not hasattr(self, '_coordinator'):
            from src.agents.coordinator import AgentCoordinator
            self._coordinator = AgentCoordinator(self)
        return self._coordinator
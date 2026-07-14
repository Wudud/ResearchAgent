"""
对话仓库测试模块 - 测试ConversationRepository的CRUD操作。

验证对话创建、消息管理、级联删除和排序功能。
"""

import pytest

from src.persistence.conversation_repository import ConversationRepository


class TestConversationRepository:
    """测试ConversationRepository的各项功能。"""

    @pytest.fixture
    def repo(self):
        """创建内存数据库的ConversationRepository实例。"""
        return ConversationRepository(db_path=":memory:")

    def test_create_conversation(self, repo):
        """测试创建对话。"""
        conv_id = repo.create_conversation()
        assert len(conv_id) > 0
        conv = repo.get_conversation(conv_id)
        assert conv is not None

    def test_list_conversations(self, repo):
        """测试列出所有对话。"""
        repo.create_conversation()
        repo.create_conversation()
        convs = repo.list_conversations()
        assert len(convs) == 2

    def test_delete_conversation(self, repo):
        """测试删除对话。"""
        conv_id = repo.create_conversation()
        repo.delete_conversation(conv_id)
        assert repo.get_conversation(conv_id) is None

    def test_delete_cascades_messages(self, repo):
        """测试删除对话时消息级联删除。"""
        conv_id = repo.create_conversation()
        repo.add_message(conv_id, "user", "hello")
        repo.delete_conversation(conv_id)
        assert repo.get_messages(conv_id) == []

    def test_add_message(self, repo):
        """测试添加消息。"""
        conv_id = repo.create_conversation()
        repo.add_message(conv_id, "user", "test message", metadata={"key": "val"})
        msgs = repo.get_messages(conv_id)
        assert len(msgs) == 1
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "test message"

    def test_get_messages_limit(self, repo):
        """测试消息获取数量限制。"""
        conv_id = repo.create_conversation()
        for i in range(30):
            repo.add_message(conv_id, "user", f"msg {i}")
        msgs = repo.get_messages(conv_id)
        assert len(msgs) == 30

    def test_update_title(self, repo):
        """测试更新对话标题。"""
        conv_id = repo.create_conversation()
        repo.update_title(conv_id, "New Title")
        conv = repo.get_conversation(conv_id)
        assert conv is not None

    def test_messages_ordered_by_id(self, repo):
        """测试消息按ID排序。"""
        conv_id = repo.create_conversation()
        repo.add_message(conv_id, "user", "first")
        repo.add_message(conv_id, "assistant", "second")
        msgs = repo.get_messages(conv_id)
        assert msgs[0]["content"] == "first"
        assert msgs[1]["content"] == "second"

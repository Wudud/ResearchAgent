import os
import tempfile
from pathlib import Path

import pytest
import yaml

from src.config.config_manager import ConfigManager
from src.utils.exceptions import ConfigError

class TestConfigManager:
    def test_load_yaml(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("app:\n  name: TestApp\n  version: '1.0'\n")
            f.flush()

        try:
            config = ConfigManager(f.name)
            assert config.get("app.name") == "TestApp"
            assert config.get("app.version") == "1.0"
        finally:
            os.unlink(f.name)

    def test_dot_path_nested_access(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("a:\n  b:\n    c: 42\n")
            f.flush()

        try:
            config = ConfigManager(f.name)
            assert config.get("a.b.c") == 42
        finally:
            os.unlink(f.name)

    def test_default_value(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("key: value\n")
            f.flush()

        try:
            config = ConfigManager(f.name)
            assert config.get("nonexistent", "default") == "default"
            assert config.get("nonexistent") is None
        finally:
            os.unlink(f.name)

    def test_env_var_resolution(self, monkeypatch):
        monkeypatch.setenv("TEST_API_KEY", "sk-test-12345")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("api_key: ${TEST_API_KEY}\n")
            f.flush()

        try:
            config = ConfigManager(f.name)
            assert config.get("api_key") == "sk-test-12345"
        finally:
            os.unlink(f.name)

    def test_missing_env_var_raises_error(self, monkeypatch):
        monkeypatch.delenv("MISSING_VAR", raising=False)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("key: ${MISSING_VAR}\n")
            f.flush()

        try:
            with pytest.raises(ConfigError, match="MISSING_VAR"):
                ConfigManager(f.name)
        finally:
            os.unlink(f.name)

    def test_file_not_found(self):
        with pytest.raises(ConfigError, match="not found"):
            ConfigManager("/nonexistent/config.yaml")

    def test_data_property(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("foo: bar\n")
            f.flush()

        try:
            config = ConfigManager(f.name)
            assert isinstance(config.data, dict)
            assert config.data["foo"] == "bar"
        finally:
            os.unlink(f.name)

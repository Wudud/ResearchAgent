import logging
from pathlib import Path

class PromptService:
    def __init__(self, prompts_dir: str = None):
        if prompts_dir is None:
            prompts_dir = Path(__file__).parent.parent.parent / "prompts"

        self._prompts_dir = Path(prompts_dir)
        self._logger = logging.getLogger("ResearchAgent.PromptService")
        self._cache: dict[str, str] = {}

    def load(self, name: str) -> str:
        if name in self._cache:
            return self._cache[name]

        file_path = self._prompts_dir / name
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            template = f.read()

        self._cache[name] = template
        self._logger.info(f"Prompt loaded: {name}")
        return template

    def render(self, name: str, **kwargs) -> str:
        template = self.load(name)
        try:
            return template.format(**kwargs)
        except KeyError as e:
            raise ValueError(
                f"Missing template variable '{e.args[0]}' in prompt '{name}'"
            )

    def reload(self, name: str = None):
        if name:
            self._cache.pop(name, None)
        else:
            self._cache.clear()

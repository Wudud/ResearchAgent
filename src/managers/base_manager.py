import logging

class BaseManager:
    def __init__(self, name: str, agent=None):
        self.name = name
        self._agent = agent

    @property
    def llm(self):
        return self._agent.llm_service if self._agent else None

    @property
    def tools(self):
        return self._agent.tools if self._agent else {}

    @property
    def config(self):
        return self._agent.config if self._agent else None

    @property
    def logger(self):
        return self._agent.logger if self._agent else None

    @property
    def services(self):
        return self._agent.services if self._agent else {}

    def initialize(self):
        if self.logger:
            self.logger.info(f"[Manager] {self.name} initialized.")
        else:
            print(f"[Manager] {self.name} initialized.")

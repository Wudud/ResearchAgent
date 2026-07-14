from abc import ABC, abstractmethod


class BaseASRAdapter(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str, language: str = None) -> str:
        ...

    @property
    @abstractmethod
    def provider(self) -> str:
        ...

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class ProviderError(RuntimeError):
    pass


class BaseProvider(ABC):
    provider_name: str

    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def analyze(self, audio_path: Path, prompt: str) -> dict[str, Any]:
        """Run one provider call for one audio file."""


def response_envelope(
    *,
    provider: str,
    model: str,
    status: str,
    response: Any = None,
    error: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "provider": provider,
        "model": model,
        "status": status,
        "response": response,
        "error": error,
        "metadata": metadata or {},
    }


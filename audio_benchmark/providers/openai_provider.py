from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .base import BaseProvider, ProviderError, response_envelope


class OpenAIProvider(BaseProvider):
    provider_name = "openai"

    def __init__(self, model: str):
        super().__init__(model)
        if not os.getenv("OPENAI_API_KEY"):
            raise ProviderError("OpenAI API key is not configured")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderError("openai is not installed") from exc
        self.client = OpenAI()

    def analyze(self, audio_path: Path, prompt: str) -> dict[str, Any]:
        try:
            with audio_path.open("rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    response_format="json",
                )
            payload = _json_safe(response)
            transcript = _extract_text(payload)
            return response_envelope(
                provider=self.provider_name,
                model=self.model,
                status="success",
                response={
                    "transcript": transcript,
                    "language": payload.get("language", "") if isinstance(payload, dict) else "",
                    "segments": payload.get("segments", []) if isinstance(payload, dict) else [],
                    "words": payload.get("words", []) if isinstance(payload, dict) else [],
                    "provider_capabilities": {
                        "nonverbal_tags": "not_supported",
                        "emotion_tags": "not_supported",
                    },
                    "sdk_response": payload,
                },
                metadata={"prompt_ignored": True},
            )
        except Exception as exc:  # noqa: BLE001 - provider errors need to be captured.
            return response_envelope(
                provider=self.provider_name,
                model=self.model,
                status="error",
                error=type(exc).__name__ + ": " + str(exc),
            )


def _extract_text(payload: Any) -> str:
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        return str(payload.get("text") or payload.get("transcript") or "")
    return str(getattr(payload, "text", "") or "")


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if hasattr(value, "model_dump"):
        return _json_safe(value.model_dump())
    if hasattr(value, "to_dict"):
        return _json_safe(value.to_dict())
    return str(value)


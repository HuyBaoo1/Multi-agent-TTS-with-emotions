from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .base import BaseProvider, ProviderError, response_envelope


class ElevenLabsProvider(BaseProvider):
    provider_name = "elevenlabs"
    endpoint = "https://api.elevenlabs.io/v1/speech-to-text"

    def __init__(self, model: str):
        super().__init__(model)
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            raise ProviderError("ElevenLabs API key is not configured")
        try:
            import requests
        except ImportError as exc:
            raise ProviderError("requests is not installed") from exc
        self.requests = requests

    def analyze(self, audio_path: Path, prompt: str) -> dict[str, Any]:
        try:
            with audio_path.open("rb") as audio_file:
                response = self.requests.post(
                    self.endpoint,
                    headers={"xi-api-key": self.api_key},
                    data={
                        "model_id": self.model,
                        "diarize": "true",
                        "tag_audio_events": "true",
                    },
                    files={"file": (audio_path.name, audio_file)},
                    timeout=180,
                )
            if response.status_code >= 400:
                return response_envelope(
                    provider=self.provider_name,
                    model=self.model,
                    status="error",
                    error=f"HTTP {response.status_code}: {response.text[:1000]}",
                )
            payload = response.json()
            return response_envelope(
                provider=self.provider_name,
                model=self.model,
                status="success",
                response=payload,
                metadata={
                    "prompt_ignored": True,
                    "requested_diarization": True,
                    "requested_audio_event_tags": True,
                },
            )
        except Exception as exc:  # noqa: BLE001 - provider errors need to be captured.
            return response_envelope(
                provider=self.provider_name,
                model=self.model,
                status="error",
                error=type(exc).__name__ + ": " + str(exc),
            )

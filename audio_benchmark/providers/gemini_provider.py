from __future__ import annotations

import json
import mimetypes
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .base import BaseProvider, ProviderError, response_envelope


class GeminiProvider(BaseProvider):
    provider_name = "gemini"

    def __init__(self, model: str):
        super().__init__(model)
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ProviderError("Gemini API key is not configured")
        try:
            from google import genai
        except ImportError as exc:
            raise ProviderError("google-genai is not installed") from exc
        self.client = genai.Client(api_key=api_key)

    def analyze(self, audio_path: Path, prompt: str) -> dict[str, Any]:
        mime_type = mimetypes.guess_type(str(audio_path))[0] or "audio/mpeg"
        uploaded_file = None
        temp_dir = None
        try:
            upload_path = audio_path
            if not str(audio_path).isascii():
                temp_dir = tempfile.TemporaryDirectory(prefix="audio_benchmark_gemini_")
                upload_path = Path(temp_dir.name) / f"audio{audio_path.suffix.lower() or '.bin'}"
                shutil.copy2(audio_path, upload_path)
            uploaded_file = self.client.files.upload(file=str(upload_path))
            response = self.client.models.generate_content(
                model=self.model,
                contents=[prompt, uploaded_file],
                config={
                    "response_mime_type": "application/json",
                    "temperature": 0,
                },
            )
            text = getattr(response, "text", "") or ""
            parsed = _parse_json_text(text)
            return response_envelope(
                provider=self.provider_name,
                model=self.model,
                status="success",
                response={
                    "parsed": parsed,
                    "text": text,
                    "mime_type": mime_type,
                    "sdk_response": _json_safe(response),
                },
            )
        except Exception as exc:  # noqa: BLE001 - provider errors need to be captured.
            return response_envelope(
                provider=self.provider_name,
                model=self.model,
                status="error",
                error=type(exc).__name__ + ": " + str(exc),
                metadata={"mime_type": mime_type},
            )
        finally:
            if uploaded_file is not None:
                _best_effort_delete_file(self.client, uploaded_file)
            if temp_dir is not None:
                temp_dir.cleanup()


def _parse_json_text(text: str) -> dict[str, Any] | None:
    if not text.strip():
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if hasattr(value, "model_dump"):
        return _json_safe(value.model_dump())
    if hasattr(value, "to_json_dict"):
        return _json_safe(value.to_json_dict())
    return str(value)


def _best_effort_delete_file(client: Any, uploaded_file: Any) -> None:
    name = getattr(uploaded_file, "name", None)
    if not name:
        return
    try:
        client.files.delete(name=name)
    except Exception:
        return

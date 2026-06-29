from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - lets dry-run work before dependencies are installed.
    def load_dotenv(*args, **kwargs):
        return False


PROMPT_VERSION = "audio_context_v1"
DEFAULT_PROVIDERS = ("gemini", "openai", "elevenlabs")
DEFAULT_MODELS_BY_PROVIDER = {
    "gemini": ("gemini-3.5-flash",),
    "openai": ("gpt-4o-mini-transcribe",),
    "elevenlabs": ("scribe_v2",),
}
OPTIONAL_MODELS_BY_PROVIDER = {
    "gemini": ("gemini-3.1-pro-preview",),
}
SUPPORTED_AUDIO_EXTENSIONS = {
    ".mp3",
    ".wav",
    ".m4a",
    ".flac",
    ".ogg",
    ".aac",
    ".webm",
    ".mp4",
}


@dataclass
class BenchmarkConfig:
    audio_dir: Path
    output_dir: Path
    providers: list[str] = field(default_factory=lambda: list(DEFAULT_PROVIDERS))
    models: list[str] | None = None
    limit: int | None = None
    dry_run: bool = False
    force_refresh: bool = False
    prompt_version: str = PROMPT_VERSION
    prompt_path: Path = Path("audio_benchmark/prompts/audio_context_prompt.txt")
    ground_truth_path: Path | None = None

    @property
    def raw_dir(self) -> Path:
        return self.output_dir / "raw"

    @property
    def normalized_dir(self) -> Path:
        return self.output_dir / "normalized"

    @property
    def reports_dir(self) -> Path:
        return self.output_dir / "reports"

    def ensure_dirs(self) -> None:
        for path in (self.raw_dir, self.normalized_dir, self.reports_dir):
            path.mkdir(parents=True, exist_ok=True)


def load_environment(env_path: str | Path = ".env") -> None:
    load_dotenv(env_path)


def parse_csv(value: str | None) -> list[str] | None:
    if value is None:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def parse_bool(value: str | bool | None, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def api_key_status() -> dict[str, bool]:
    return {
        "gemini": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "elevenlabs": bool(os.getenv("ELEVENLABS_API_KEY")),
    }


def discover_audio_files(audio_dir: Path, limit: int | None = None) -> list[Path]:
    files = [
        path
        for path in audio_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
    ]
    files = sorted(files, key=lambda path: str(path).lower())
    if limit is not None:
        return files[:limit]
    return files


def resolve_provider_models(
    providers: Iterable[str],
    models: Iterable[str] | None,
) -> list[tuple[str, str]]:
    requested_models = set(models or [])
    pairs: list[tuple[str, str]] = []
    for provider in providers:
        provider = provider.strip().lower()
        defaults = DEFAULT_MODELS_BY_PROVIDER.get(provider, ())
        optionals = OPTIONAL_MODELS_BY_PROVIDER.get(provider, ())
        known = set(defaults + optionals)
        if requested_models:
            selected = [model for model in requested_models if model in known]
            if provider == "openai":
                selected += [model for model in requested_models if model.startswith("gpt-") or "transcribe" in model]
            if provider == "gemini":
                selected += [model for model in requested_models if model.startswith("gemini-")]
            if provider == "elevenlabs":
                selected += [model for model in requested_models if model.startswith("scribe")]
            selected = sorted(set(selected))
        else:
            selected = list(defaults)
        pairs.extend((provider, model) for model in selected)
    return pairs

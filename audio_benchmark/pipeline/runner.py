from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from audio_benchmark.cache import (
    NormalizedStore,
    ResponseCache,
    build_file_id,
    cache_key,
    sha256_file,
    sha256_text,
)
from audio_benchmark.config import BenchmarkConfig, discover_audio_files, resolve_provider_models
from audio_benchmark.pipeline.evaluator import evaluate, load_ground_truth
from audio_benchmark.pipeline.normalizer import normalize_raw_result
from audio_benchmark.pipeline.report import write_reports
from audio_benchmark.providers.base import ProviderError, response_envelope
from audio_benchmark.providers.elevenlabs_provider import ElevenLabsProvider
from audio_benchmark.providers.gemini_provider import GeminiProvider
from audio_benchmark.providers.openai_provider import OpenAIProvider


PROVIDER_CLASSES = {
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "elevenlabs": ElevenLabsProvider,
}


def run_benchmark(config: BenchmarkConfig) -> dict[str, Any]:
    config.ensure_dirs()
    prompt = config.prompt_path.read_text(encoding="utf-8")
    prompt_hash = sha256_text(prompt)
    audio_files = discover_audio_files(config.audio_dir, config.limit)
    provider_models = resolve_provider_models(config.providers, config.models)
    response_cache = ResponseCache(config.raw_dir)
    normalized_store = NormalizedStore(config.normalized_dir)

    plan = _build_plan(audio_files, provider_models, response_cache, config, prompt_hash)
    if config.dry_run:
        return {
            "dry_run": True,
            "audio_files": len(audio_files),
            "provider_models": provider_models,
            "planned_tasks": len(plan),
            "planned_api_calls": sum(1 for item in plan if item["needs_api_call"]),
            "cached_tasks": sum(1 for item in plan if not item["needs_api_call"]),
            "reports_dir": str(config.reports_dir),
            "normalized_path": str(normalized_store.path),
        }

    provider_instances: dict[tuple[str, str], Any] = {}
    provider_errors: dict[tuple[str, str], str] = {}
    api_calls = 0
    cached = 0
    skipped = 0
    errors = 0

    for item in plan:
        cached_payload = None if config.force_refresh else response_cache.read_if_valid(item["raw_path"], item["cache_key"])
        if cached_payload is not None:
            raw_payload = cached_payload
            cached += 1
        else:
            provider_key = (item["provider"], item["model"])
            if provider_key in provider_errors:
                raw_payload = _raw_payload(item, response_envelope(
                    provider=item["provider"],
                    model=item["model"],
                    status="skipped",
                    error=provider_errors[provider_key],
                ))
                skipped += 1
            else:
                provider = provider_instances.get(provider_key)
                if provider is None:
                    provider = _create_provider(item["provider"], item["model"], provider_errors)
                    if provider is not None:
                        provider_instances[provider_key] = provider
                if provider is None:
                    raw_payload = _raw_payload(item, response_envelope(
                        provider=item["provider"],
                        model=item["model"],
                        status="skipped",
                        error=provider_errors[provider_key],
                    ))
                    skipped += 1
                else:
                    provider_response = provider.analyze(item["audio_path"], prompt)
                    raw_payload = _raw_payload(item, provider_response)
                    response_cache.write(item["raw_path"], raw_payload)
                    api_calls += 1
                    if provider_response.get("status") == "error":
                        errors += 1

        normalized = normalize_raw_result(
            raw_payload=raw_payload,
            file_id=item["file_id"],
            file_path=item["audio_path"],
            provider=item["provider"],
            model=item["model"],
            raw_response_path=item["raw_path"],
        )
        normalized_store.upsert(normalized)

    records = normalized_store.all_records()
    ground_truth = load_ground_truth(config.ground_truth_path)
    metrics = evaluate(records, ground_truth)
    write_reports(metrics, config.reports_dir)

    return {
        "dry_run": False,
        "audio_files": len(audio_files),
        "provider_models": provider_models,
        "tasks": len(plan),
        "api_calls": api_calls,
        "cached": cached,
        "skipped": skipped,
        "errors": errors,
        "normalized_path": str(normalized_store.path),
        "reports_dir": str(config.reports_dir),
    }


def _build_plan(
    audio_files: list[Path],
    provider_models: list[tuple[str, str]],
    response_cache: ResponseCache,
    config: BenchmarkConfig,
    prompt_hash: str,
) -> list[dict[str, Any]]:
    plan = []
    for audio_path in audio_files:
        file_hash = sha256_file(audio_path)
        file_id = build_file_id(audio_path, file_hash)
        for provider, model in provider_models:
            key = cache_key(file_hash, provider, model, config.prompt_version, prompt_hash)
            raw_path = response_cache.raw_path(provider, model, file_id)
            cached_payload = None if config.force_refresh else response_cache.read_if_valid(raw_path, key)
            plan.append(
                {
                    "audio_path": audio_path,
                    "file_hash": file_hash,
                    "file_id": file_id,
                    "provider": provider,
                    "model": model,
                    "prompt_version": config.prompt_version,
                    "prompt_hash": prompt_hash,
                    "cache_key": key,
                    "raw_path": raw_path,
                    "needs_api_call": cached_payload is None,
                }
            )
    return plan


def _create_provider(provider: str, model: str, provider_errors: dict[tuple[str, str], str]) -> Any | None:
    provider_class = PROVIDER_CLASSES.get(provider)
    if provider_class is None:
        provider_errors[(provider, model)] = f"Provider is not implemented: {provider}"
        return None
    try:
        return provider_class(model)
    except ProviderError as exc:
        provider_errors[(provider, model)] = str(exc)
        return None


def _raw_payload(item: dict[str, Any], provider_response: dict[str, Any]) -> dict[str, Any]:
    return {
        "cache_key": item["cache_key"],
        "prompt_version": item["prompt_version"],
        "prompt_hash": item["prompt_hash"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "file_id": item["file_id"],
        "file_path": str(item["audio_path"]),
        "file_hash": item["file_hash"],
        "provider": item["provider"],
        "model": item["model"],
        "provider_response": provider_response,
    }


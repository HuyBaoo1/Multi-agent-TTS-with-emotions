from __future__ import annotations

import argparse
from pathlib import Path

from audio_benchmark.config import (
    BenchmarkConfig,
    api_key_status,
    load_environment,
    parse_bool,
    parse_csv,
)
from audio_benchmark.pipeline.runner import run_benchmark


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one-pass audio understanding benchmark.")
    parser.add_argument("--audio_dir", default="audio/Audio-short", help="Directory containing audio files.")
    parser.add_argument("--output_dir", default="audio_benchmark/outputs", help="Directory for raw, normalized, and report outputs.")
    parser.add_argument("--providers", default="gemini,openai,elevenlabs", help="Comma-separated providers.")
    parser.add_argument("--models", default=None, help="Comma-separated model names.")
    parser.add_argument("--limit", type=int, default=None, help="Only process first N audio files.")
    parser.add_argument("--dry_run", action="store_true", help="Show planned API calls without calling APIs.")
    parser.add_argument("--force_refresh", default="false", help="true/false; ignore cache when true.")
    parser.add_argument("--ground_truth", default=None, help="Optional JSON or CSV ground-truth transcript file.")
    args = parser.parse_args()

    load_environment()
    config = BenchmarkConfig(
        audio_dir=Path(args.audio_dir),
        output_dir=Path(args.output_dir),
        providers=parse_csv(args.providers) or [],
        models=parse_csv(args.models),
        limit=args.limit,
        dry_run=args.dry_run,
        force_refresh=parse_bool(args.force_refresh, default=False),
        ground_truth_path=Path(args.ground_truth) if args.ground_truth else None,
    )

    key_status = api_key_status()
    print("API keys found:", ", ".join(f"{provider}={present}" for provider, present in key_status.items()))
    summary = run_benchmark(config)
    if summary["dry_run"]:
        print(f"Dry run: {summary['audio_files']} audio file(s), {len(summary['provider_models'])} model target(s)")
        print(f"Planned tasks: {summary['planned_tasks']}")
        print(f"Planned API calls: {summary['planned_api_calls']}")
        print(f"Cached tasks: {summary['cached_tasks']}")
    else:
        print(f"Completed tasks: {summary['tasks']}")
        print(f"API calls made: {summary['api_calls']}")
        print(f"Cached tasks reused: {summary['cached']}")
        print(f"Skipped tasks: {summary['skipped']}")
        print(f"API/provider errors: {summary['errors']}")
    print(f"Normalized results: {summary['normalized_path']}")
    print(f"Reports: {summary['reports_dir']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


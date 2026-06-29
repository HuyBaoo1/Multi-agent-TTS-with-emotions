from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_name(value: str, max_len: int = 80) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return (cleaned or "audio")[:max_len]


def build_file_id(audio_path: Path, file_hash: str) -> str:
    return f"{safe_name(audio_path.stem)}_{file_hash[:12]}"


def cache_key(file_hash: str, provider: str, model: str, prompt_version: str, prompt_hash: str) -> str:
    return sha256_text("|".join([file_hash, provider, model, prompt_version, prompt_hash]))


class ResponseCache:
    def __init__(self, raw_dir: Path):
        self.raw_dir = raw_dir
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def raw_path(self, provider: str, model: str, file_id: str) -> Path:
        return self.raw_dir / f"{safe_name(provider)}_{safe_name(model)}_{file_id}.json"

    def read_if_valid(self, path: Path, expected_cache_key: str) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if payload.get("cache_key") != expected_cache_key:
            return None
        return payload

    def write(self, path: Path, payload: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(path)


class NormalizedStore:
    def __init__(self, normalized_dir: Path):
        self.path = normalized_dir / "audio_context_results.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.records: dict[str, dict[str, Any]] = {}
        self.load()

    @staticmethod
    def record_key(record: dict[str, Any]) -> str:
        return "|".join([record.get("file_id", ""), record.get("provider", ""), record.get("model", "")])

    def load(self) -> None:
        if not self.path.exists():
            return
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            self.records[self.record_key(record)] = record

    def upsert(self, record: dict[str, Any]) -> None:
        self.records[self.record_key(record)] = record
        self.flush()

    def flush(self) -> None:
        temp_path = self.path.with_suffix(".jsonl.tmp")
        lines = [
            json.dumps(record, ensure_ascii=False, sort_keys=True)
            for _, record in sorted(self.records.items())
        ]
        temp_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        temp_path.replace(self.path)

    def all_records(self) -> list[dict[str, Any]]:
        return [record for _, record in sorted(self.records.items())]


from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any


RELIABILITY_WEIGHTS = {
    "coverage_score": 25.0,
    "transcript_quality_score": 25.0,
    "nonverbal_tag_score": 15.0,
    "emotion_agreement_score": 15.0,
    "error_penalty": 30.0,
    "unsupported_field_penalty": 5.0,
}


def load_ground_truth(path: Path | None) -> dict[str, str]:
    if not path or not path.exists():
        return {}
    if path.suffix.lower() == ".json":
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return {str(key): str(value) for key, value in payload.items()}
        if isinstance(payload, list):
            return {
                str(item.get("file_id") or item.get("file_path") or item.get("file_name")): str(item.get("transcript", ""))
                for item in payload
                if isinstance(item, dict)
            }
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            return {
                str(row.get("file_id") or row.get("file_path") or row.get("file_name")): str(row.get("transcript", ""))
                for row in reader
            }
    return {}


def evaluate(records: list[dict[str, Any]], ground_truth: dict[str, str] | None = None) -> dict[str, list[dict[str, Any]]]:
    ground_truth = ground_truth or {}
    grouped_model = defaultdict(list)
    grouped_file = defaultdict(list)
    for record in records:
        grouped_model[_model_key(record)].append(record)
        grouped_file[record["file_id"]].append(record)

    peer_similarity = _peer_transcript_similarity(grouped_file)
    nonverbal_agreement = _peer_tag_jaccard(grouped_file, "nonverbal_tags", include_background=True)
    emotion_agreement = _peer_emotion_agreement(grouped_file)

    model_rows = []
    transcription_rows = []
    nonverbal_rows = []
    emotion_rows = []
    reliability_rows = []
    error_rows = []

    for key, model_records in sorted(grouped_model.items()):
        provider, model = key
        total = len(model_records)
        success = [record for record in model_records if record["status"] == "success"]
        errors = [record for record in model_records if record["status"] == "error"]
        skipped = [record for record in model_records if record["status"] == "skipped"]
        transcripts = [_transcript(record) for record in model_records]
        nonempty = [text for text in transcripts if text.strip()]
        coverage_rate = len(success) / total if total else 0.0
        empty_transcript_rate = (len(transcripts) - len(nonempty)) / total if total else 0.0
        api_error_rate = len(errors) / total if total else 0.0
        unsupported_count = _unsupported_count(provider, model)

        wers = []
        cers = []
        for record in model_records:
            truth = _truth_for_record(record, ground_truth)
            if truth is None:
                continue
            wers.append(word_error_rate(truth, _transcript(record)))
            cers.append(char_error_rate(truth, _transcript(record)))

        avg_peer_similarity = _average_for_model(peer_similarity, key)
        avg_nonverbal_jaccard = _average_for_model(nonverbal_agreement, key)
        avg_emotion_agreement = _average_for_model(emotion_agreement, key)
        tag_counts = [_tag_count(record) for record in model_records]
        emotion_labels = [_emotion_label(record) for record in model_records]
        uncertain_rate = _rate(emotion_labels, "uncertain_emotion")
        not_applicable_rate = _rate(emotion_labels, "not_applicable")

        reliability_components = {
            "coverage_score": coverage_rate * RELIABILITY_WEIGHTS["coverage_score"],
            "transcript_quality_score": (1.0 - empty_transcript_rate) * RELIABILITY_WEIGHTS["transcript_quality_score"],
            "nonverbal_tag_score": min(sum(tag_counts) / max(total, 1), 1.0) * RELIABILITY_WEIGHTS["nonverbal_tag_score"],
            "emotion_agreement_score": avg_emotion_agreement * RELIABILITY_WEIGHTS["emotion_agreement_score"],
            "error_penalty": api_error_rate * RELIABILITY_WEIGHTS["error_penalty"],
            "unsupported_field_penalty": unsupported_count * RELIABILITY_WEIGHTS["unsupported_field_penalty"],
        }
        reliability_score = (
            reliability_components["coverage_score"]
            + reliability_components["transcript_quality_score"]
            + reliability_components["nonverbal_tag_score"]
            + reliability_components["emotion_agreement_score"]
            - reliability_components["error_penalty"]
            - reliability_components["unsupported_field_penalty"]
        )

        model_rows.append(
            {
                "provider": provider,
                "model": model,
                "total_files": total,
                "success": len(success),
                "errors": len(errors),
                "skipped": len(skipped),
                "coverage_rate": coverage_rate,
                "empty_transcript_rate": empty_transcript_rate,
                "api_error_rate": api_error_rate,
                "avg_tags_detected": sum(tag_counts) / total if total else 0.0,
            }
        )
        transcription_rows.append(
            {
                "provider": provider,
                "model": model,
                "total_files": total,
                "coverage_rate": coverage_rate,
                "empty_transcript_rate": empty_transcript_rate,
                "avg_peer_transcript_similarity": avg_peer_similarity,
                "wer": _avg(wers),
                "cer": _avg(cers),
                "ground_truth_items": len(wers),
            }
        )
        nonverbal_rows.append(
            {
                "provider": provider,
                "model": model,
                "avg_nonverbal_background_tags": sum(tag_counts) / total if total else 0.0,
                "avg_peer_jaccard": avg_nonverbal_jaccard,
                "unsupported_fields": unsupported_count,
                "global_tag_count": sum(_global_tag_count(record) for record in model_records),
                "timestamped_tag_count": sum(_timestamped_tag_count(record) for record in model_records),
            }
        )
        emotion_rows.append(
            {
                "provider": provider,
                "model": model,
                "avg_peer_emotion_agreement": avg_emotion_agreement,
                "uncertain_emotion_rate": uncertain_rate,
                "not_applicable_rate": not_applicable_rate,
                "emotion_label_counts": json.dumps(Counter(emotion_labels), ensure_ascii=False),
            }
        )
        reliability_rows.append(
            {
                "provider": provider,
                "model": model,
                "reliability_score": round(reliability_score, 4),
                **{key: round(value, 4) for key, value in reliability_components.items()},
            }
        )
        for record in errors + skipped:
            error_rows.append(
                {
                    "provider": provider,
                    "model": model,
                    "file_id": record.get("file_id", ""),
                    "status": record.get("status", ""),
                    "error": record.get("error", ""),
                }
            )

    return {
        "model_comparison": model_rows,
        "transcription_metrics": transcription_rows,
        "nonverbal_metrics": nonverbal_rows,
        "emotion_metrics": emotion_rows,
        "reliability_summary": sorted(reliability_rows, key=lambda row: row["reliability_score"], reverse=True),
        "error_report": error_rows,
    }


def word_error_rate(reference: str, hypothesis: str) -> float:
    return _edit_distance(reference.split(), hypothesis.split()) / max(len(reference.split()), 1)


def char_error_rate(reference: str, hypothesis: str) -> float:
    return _edit_distance(list(reference), list(hypothesis)) / max(len(reference), 1)


def _edit_distance(reference: list[str], hypothesis: list[str]) -> int:
    previous = list(range(len(hypothesis) + 1))
    for i, ref_token in enumerate(reference, start=1):
        current = [i]
        for j, hyp_token in enumerate(hypothesis, start=1):
            cost = 0 if ref_token == hyp_token else 1
            current.append(min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost))
        previous = current
    return previous[-1]


def _peer_transcript_similarity(grouped_file: dict[str, list[dict[str, Any]]]) -> dict[tuple[str, str], list[float]]:
    scores = defaultdict(list)
    for records in grouped_file.values():
        for left, right in _pairs(records):
            ratio = SequenceMatcher(None, _transcript(left), _transcript(right)).ratio()
            scores[_model_key(left)].append(ratio)
            scores[_model_key(right)].append(ratio)
    return scores


def _peer_tag_jaccard(
    grouped_file: dict[str, list[dict[str, Any]]],
    field: str,
    include_background: bool = False,
) -> dict[tuple[str, str], list[float]]:
    scores = defaultdict(list)
    for records in grouped_file.values():
        for left, right in _pairs(records):
            left_tags = _tag_set(left, field, include_background)
            right_tags = _tag_set(right, field, include_background)
            union = left_tags | right_tags
            score = 1.0 if not union else len(left_tags & right_tags) / len(union)
            scores[_model_key(left)].append(score)
            scores[_model_key(right)].append(score)
    return scores


def _peer_emotion_agreement(grouped_file: dict[str, list[dict[str, Any]]]) -> dict[tuple[str, str], list[float]]:
    scores = defaultdict(list)
    for records in grouped_file.values():
        for left, right in _pairs(records):
            score = 1.0 if _emotion_label(left) == _emotion_label(right) else 0.0
            scores[_model_key(left)].append(score)
            scores[_model_key(right)].append(score)
    return scores


def _pairs(records: list[dict[str, Any]]):
    for index, left in enumerate(records):
        for right in records[index + 1 :]:
            yield left, right


def _model_key(record: dict[str, Any]) -> tuple[str, str]:
    return record.get("provider", ""), record.get("model", "")


def _transcript(record: dict[str, Any]) -> str:
    return str((record.get("transcription") or {}).get("transcript") or "")


def _tag_set(record: dict[str, Any], field: str, include_background: bool = False) -> set[str]:
    tags = {str(tag.get("label")) for tag in record.get(field, []) if isinstance(tag, dict)}
    if include_background:
        tags |= {str(tag.get("label")) for tag in record.get("noise_background_tags", []) if isinstance(tag, dict)}
    return {tag for tag in tags if tag}


def _tag_count(record: dict[str, Any]) -> int:
    return len(record.get("nonverbal_tags", [])) + len(record.get("noise_background_tags", []))


def _global_tag_count(record: dict[str, Any]) -> int:
    return sum(1 for tag in record.get("nonverbal_tags", []) + record.get("noise_background_tags", []) if tag.get("time_status") == "global")


def _timestamped_tag_count(record: dict[str, Any]) -> int:
    return sum(1 for tag in record.get("nonverbal_tags", []) + record.get("noise_background_tags", []) if tag.get("time_status") == "timestamped")


def _emotion_label(record: dict[str, Any]) -> str:
    tags = record.get("emotion_tags") or []
    if not tags:
        return ""
    first = tags[0]
    return str(first.get("label", "")) if isinstance(first, dict) else ""


def _truth_for_record(record: dict[str, Any], ground_truth: dict[str, str]) -> str | None:
    keys = [
        record.get("file_id", ""),
        record.get("file_path", ""),
        Path(record.get("file_path", "")).name,
        Path(record.get("file_path", "")).stem,
    ]
    for key in keys:
        if key in ground_truth:
            return ground_truth[key]
    return None


def _unsupported_count(provider: str, model: str) -> int:
    if provider == "openai":
        return 2
    if provider == "elevenlabs":
        return 1
    return 0


def _average_for_model(scores: dict[tuple[str, str], list[float]], key: tuple[str, str]) -> float:
    return _avg(scores.get(key, []))


def _avg(values: list[float]) -> float | str:
    if not values:
        return ""
    return sum(values) / len(values)


def _rate(values: list[str], target: str) -> float:
    return values.count(target) / len(values) if values else 0.0


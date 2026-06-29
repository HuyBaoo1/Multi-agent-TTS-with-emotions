from __future__ import annotations

from pathlib import Path
from typing import Any

from audio_benchmark.schemas import (
    CONFIDENCE_LEVELS,
    EMOTION_LABELS,
    NOISE_LEVELS,
    NONVERBAL_LABELS,
    RAW_EMOTION_ALIASES,
    RAW_NONVERBAL_ALIASES,
    empty_result,
)


BACKGROUND_LABELS = {
    "music",
    "background_noise",
    "traffic",
    "rain",
    "door_sound",
    "phone_ring",
    "alarm",
    "silence",
    "unknown_sound",
}


def normalize_raw_result(
    *,
    raw_payload: dict[str, Any],
    file_id: str,
    file_path: Path,
    provider: str,
    model: str,
    raw_response_path: Path,
) -> dict[str, Any]:
    result = empty_result(
        file_id=file_id,
        file_path=str(file_path),
        provider=provider,
        model=model,
        raw_response_path=str(raw_response_path),
    )

    provider_response = raw_payload.get("provider_response", raw_payload)
    status = provider_response.get("status", "error")
    result["status"] = status
    result["error"] = provider_response.get("error")
    if status != "success":
        return result

    response = provider_response.get("response")
    if provider == "gemini":
        _normalize_gemini(response, result)
    elif provider == "openai":
        _normalize_openai(response, result)
    elif provider == "elevenlabs":
        _normalize_elevenlabs(response, result)
    else:
        result["error"] = f"Unsupported provider: {provider}"
        result["status"] = "error"

    _finalize(result)
    return result


def _normalize_gemini(response: Any, result: dict[str, Any]) -> None:
    parsed = response.get("parsed") if isinstance(response, dict) else None
    if not isinstance(parsed, dict):
        result["status"] = "error"
        result["error"] = "Gemini did not return parseable JSON"
        return
    transcription = parsed.get("transcription") or {}
    result["transcription"]["transcript"] = _string(transcription.get("transcript"))
    result["transcription"]["language"] = _string(transcription.get("language"))
    result["transcription"]["segments"] = _list(transcription.get("segments"))
    result["transcription"]["words"] = _list(transcription.get("words"))
    result["tagged_transcript"] = _string(parsed.get("tagged_transcript"))
    result["nonverbal_tags"] = _normalize_sound_tags(parsed.get("nonverbal_tags"), prefer_background=False)
    result["noise_background_tags"] = _normalize_sound_tags(parsed.get("noise_background_tags"), prefer_background=True)
    moved_background = [tag for tag in result["nonverbal_tags"] if tag["label"] in BACKGROUND_LABELS]
    result["nonverbal_tags"] = [tag for tag in result["nonverbal_tags"] if tag["label"] not in BACKGROUND_LABELS]
    result["noise_background_tags"].extend(moved_background)
    result["emotion_tags"] = _normalize_emotion_tags(parsed.get("emotion_tags"))
    result["quality"].update(_normalize_quality(parsed.get("quality")))
    result["reliability"].update(_normalize_reliability(parsed.get("reliability")))


def _normalize_openai(response: Any, result: dict[str, Any]) -> None:
    if not isinstance(response, dict):
        response = {}
    result["transcription"]["transcript"] = _string(response.get("transcript"))
    result["transcription"]["language"] = _string(response.get("language"))
    result["transcription"]["segments"] = _list(response.get("segments"))
    result["transcription"]["words"] = _list(response.get("words"))
    result["tagged_transcript"] = result["transcription"]["transcript"]
    result["nonverbal_tags"] = []
    result["noise_background_tags"] = []
    result["emotion_tags"] = []
    result["reliability"]["nonverbal_confidence"] = "unknown"
    result["reliability"]["emotion_confidence"] = "unknown"
    result["reliability"]["transcript_confidence"] = "unknown"
    result["reliability"]["overall_confidence"] = "unknown"
    result["quality"]["speech_present"] = bool(result["transcription"]["transcript"].strip())


def _normalize_elevenlabs(response: Any, result: dict[str, Any]) -> None:
    if not isinstance(response, dict):
        response = {}
    words_raw = _list(response.get("words"))
    word_items = []
    audio_event_tags = []
    speaker_ids = set()
    for item in words_raw:
        if not isinstance(item, dict):
            continue
        item_type = _string(item.get("type")).lower()
        text = _string(item.get("text") or item.get("word"))
        if item.get("speaker_id") is not None:
            speaker_ids.add(str(item.get("speaker_id")))
        if item_type in {"", "word", "spacing"}:
            if item_type != "spacing" and text.strip():
                word_items.append(item)
            continue
        audio_event_tags.append(_tag_from_event_text(text or item_type, item))

    explicit_events = _list(response.get("audio_events") or response.get("non_speech_events"))
    for event in explicit_events:
        if isinstance(event, dict):
            audio_event_tags.append(_tag_from_event_text(_string(event.get("label") or event.get("text")), event))
        else:
            audio_event_tags.append(_tag_from_event_text(_string(event), {}))

    sound_tags = [tag for tag in audio_event_tags if tag]
    result["transcription"]["transcript"] = _string(response.get("text") or response.get("transcript"))
    result["transcription"]["language"] = _string(response.get("language_code") or response.get("language"))
    result["transcription"]["segments"] = _list(response.get("segments"))
    result["transcription"]["words"] = word_items
    result["tagged_transcript"] = result["transcription"]["transcript"]
    result["nonverbal_tags"] = [tag for tag in sound_tags if tag["label"] not in BACKGROUND_LABELS]
    result["noise_background_tags"] = [tag for tag in sound_tags if tag["label"] in BACKGROUND_LABELS]
    result["emotion_tags"] = []
    result["quality"]["speech_present"] = bool(result["transcription"]["transcript"].strip())
    result["quality"]["multiple_speakers"] = len(speaker_ids) > 1
    result["reliability"]["transcript_confidence"] = "unknown"
    result["reliability"]["nonverbal_confidence"] = "unknown"
    result["reliability"]["emotion_confidence"] = "unknown"
    result["reliability"]["overall_confidence"] = "unknown"


def _finalize(result: dict[str, Any]) -> None:
    words = result["transcription"].get("words") or []
    result["transcription"]["word_timestamp_available"] = any(
        isinstance(word, dict)
        and (word.get("start") is not None or word.get("start_time") is not None)
        and (word.get("end") is not None or word.get("end_time") is not None)
        for word in words
    )
    if not result["tagged_transcript"]:
        result["tagged_transcript"] = result["transcription"].get("transcript", "")
    if not result["emotion_tags"] and not result["quality"].get("speech_present"):
        result["emotion_tags"] = [
            {
                "label": "not_applicable",
                "confidence": None,
                "evidence": "",
                "scope": "whole_audio",
            }
        ]


def _normalize_sound_tags(value: Any, prefer_background: bool) -> list[dict[str, Any]]:
    tags = []
    for item in _list(value):
        if isinstance(item, str):
            raw_label = item
            confidence = None
            evidence = ""
            time_status = "global"
        elif isinstance(item, dict):
            raw_label = _string(item.get("label") or item.get("raw_label") or item.get("type"))
            confidence = _confidence_float(item.get("confidence"))
            evidence = _string(item.get("evidence") or item.get("text"))
            time_status = _time_status(item)
        else:
            continue
        label = canonical_sound_label(raw_label)
        if not label:
            continue
        if prefer_background and label not in BACKGROUND_LABELS:
            prefer_background = False
        tags.append(
            {
                "label": label,
                "raw_label": raw_label,
                "confidence": confidence,
                "evidence": evidence,
                "time_status": time_status,
            }
        )
    return _dedupe_tags(tags)


def _normalize_emotion_tags(value: Any) -> list[dict[str, Any]]:
    tags = []
    for item in _list(value):
        if isinstance(item, str):
            raw_label = item
            confidence = None
            evidence = ""
            scope = "whole_audio"
        elif isinstance(item, dict):
            raw_label = _string(item.get("label") or item.get("emotion"))
            confidence = _confidence_float(item.get("confidence"))
            evidence = _string(item.get("evidence") or item.get("text"))
            scope = _string(item.get("scope") or "whole_audio")
        else:
            continue
        label = canonical_emotion_label(raw_label)
        if not label:
            continue
        tags.append(
            {
                "label": label,
                "confidence": confidence,
                "evidence": evidence,
                "scope": scope or "whole_audio",
            }
        )
    return _dedupe_tags(tags)


def _normalize_quality(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        "speech_present": bool(value.get("speech_present", False)),
        "noise_level": _enum(_string(value.get("noise_level")), NOISE_LEVELS, "unknown"),
        "multiple_speakers": bool(value.get("multiple_speakers", False)),
        "confidence": _enum(_string(value.get("confidence")), CONFIDENCE_LEVELS, "unknown"),
    }


def _normalize_reliability(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        "transcript_confidence": _enum(_string(value.get("transcript_confidence")), CONFIDENCE_LEVELS, "unknown"),
        "nonverbal_confidence": _enum(_string(value.get("nonverbal_confidence")), CONFIDENCE_LEVELS, "unknown"),
        "emotion_confidence": _enum(_string(value.get("emotion_confidence")), CONFIDENCE_LEVELS, "unknown"),
        "overall_confidence": _enum(_string(value.get("overall_confidence")), CONFIDENCE_LEVELS, "unknown"),
    }


def _tag_from_event_text(text: str, item: dict[str, Any]) -> dict[str, Any] | None:
    label = canonical_sound_label(text)
    if not label:
        return None
    return {
        "label": label,
        "raw_label": text,
        "confidence": _confidence_float(item.get("confidence") or item.get("score")),
        "evidence": text,
        "time_status": "timestamped" if item.get("start") is not None or item.get("start_time") is not None else "global",
    }


def canonical_sound_label(raw_label: str) -> str | None:
    normalized = raw_label.strip().lower().replace("-", " ").replace("_", " ")
    normalized = normalized.strip("[](){}:.,; ")
    if not normalized:
        return None
    if normalized in RAW_NONVERBAL_ALIASES:
        return RAW_NONVERBAL_ALIASES[normalized]
    underscored = normalized.replace(" ", "_")
    if underscored in NONVERBAL_LABELS:
        return underscored
    for alias, label in RAW_NONVERBAL_ALIASES.items():
        if alias in normalized:
            return label
    return "unknown_sound"


def canonical_emotion_label(raw_label: str) -> str | None:
    normalized = raw_label.strip().lower().replace("-", " ").replace("_", " ")
    normalized = normalized.strip("[](){}:.,; ")
    if not normalized:
        return None
    if normalized in RAW_EMOTION_ALIASES:
        return RAW_EMOTION_ALIASES[normalized]
    underscored = normalized.replace(" ", "_")
    if underscored in EMOTION_LABELS:
        return underscored
    return "uncertain_emotion"


def _dedupe_tags(tags: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    deduped = []
    for tag in tags:
        key = (tag.get("label"), tag.get("time_status"), tag.get("scope"), tag.get("evidence"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(tag)
    return deduped


def _time_status(item: dict[str, Any]) -> str:
    if item.get("time_status") in {"global", "timestamped"}:
        return item["time_status"]
    has_time = any(item.get(key) is not None for key in ("start", "end", "start_time", "end_time", "timestamp"))
    return "timestamped" if has_time else "global"


def _confidence_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, number))


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _string(value: Any) -> str:
    return "" if value is None else str(value)


def _enum(value: str, allowed: set[str], default: str) -> str:
    value = value.strip().lower()
    return value if value in allowed else default


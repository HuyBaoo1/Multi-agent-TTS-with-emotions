from __future__ import annotations

from copy import deepcopy
from typing import Any


NONVERBAL_LABELS = {
    "laughter",
    "crying",
    "cough",
    "sneeze",
    "sigh",
    "scream",
    "applause",
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

EMOTION_LABELS = {
    "neutral",
    "happy",
    "sad",
    "angry",
    "fearful",
    "calm",
    "excited",
    "stressed",
    "uncertain_emotion",
    "not_applicable",
}

CONFIDENCE_LEVELS = {"high", "medium", "low", "unknown"}
NOISE_LEVELS = {"low", "medium", "high", "unknown"}


RAW_NONVERBAL_ALIASES = {
    "laugh": "laughter",
    "laughing": "laughter",
    "giggle": "laughter",
    "giggles": "laughter",
    "cry": "crying",
    "weeping": "crying",
    "sob": "crying",
    "sobbing": "crying",
    "coughing": "cough",
    "sneezing": "sneeze",
    "sighing": "sigh",
    "yell": "scream",
    "yelling": "scream",
    "screaming": "scream",
    "clapping": "applause",
    "clap": "applause",
    "song": "music",
    "background music": "music",
    "noise": "background_noise",
    "background noise": "background_noise",
    "ambient noise": "background_noise",
    "car": "traffic",
    "cars": "traffic",
    "vehicle": "traffic",
    "vehicles": "traffic",
    "rainfall": "rain",
    "door": "door_sound",
    "doorbell": "door_sound",
    "ringtone": "phone_ring",
    "phone": "phone_ring",
    "telephone": "phone_ring",
    "siren": "alarm",
    "beep": "alarm",
    "quiet": "silence",
    "silent": "silence",
    "unknown": "unknown_sound",
}

RAW_EMOTION_ALIASES = {
    "joy": "happy",
    "joyful": "happy",
    "cheerful": "happy",
    "happiness": "happy",
    "sadness": "sad",
    "upset": "sad",
    "mad": "angry",
    "anger": "angry",
    "fear": "fearful",
    "afraid": "fearful",
    "scared": "fearful",
    "relaxed": "calm",
    "peaceful": "calm",
    "exciting": "excited",
    "enthusiastic": "excited",
    "stress": "stressed",
    "anxious": "stressed",
    "unclear": "uncertain_emotion",
    "uncertain": "uncertain_emotion",
    "unknown": "uncertain_emotion",
    "none": "not_applicable",
    "n/a": "not_applicable",
}


def empty_result(
    *,
    file_id: str,
    file_path: str,
    provider: str,
    model: str,
    status: str = "skipped",
    raw_response_path: str = "",
    error: str | None = None,
) -> dict[str, Any]:
    return {
        "file_id": file_id,
        "file_path": file_path,
        "provider": provider,
        "model": model,
        "status": status,
        "transcription": {
            "transcript": "",
            "language": "",
            "segments": [],
            "words": [],
            "word_timestamp_available": False,
        },
        "tagged_transcript": "",
        "nonverbal_tags": [],
        "noise_background_tags": [],
        "emotion_tags": [],
        "quality": {
            "speech_present": False,
            "noise_level": "unknown",
            "multiple_speakers": False,
            "confidence": "unknown",
        },
        "reliability": {
            "transcript_confidence": "unknown",
            "nonverbal_confidence": "unknown",
            "emotion_confidence": "unknown",
            "overall_confidence": "unknown",
        },
        "raw_response_path": raw_response_path,
        "error": error,
    }


def clone_empty_result(**kwargs: Any) -> dict[str, Any]:
    return deepcopy(empty_result(**kwargs))


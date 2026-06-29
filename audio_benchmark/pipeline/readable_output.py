from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from audio_benchmark.cache import safe_name


def generate_readable_outputs(input_path: Path, output_dir: Path) -> dict[str, int | str]:
    records = _load_jsonl(input_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    by_audio_dir = output_dir / "by_audio"
    by_model_dir = output_dir / "by_model"
    by_audio_dir.mkdir(parents=True, exist_ok=True)
    by_model_dir.mkdir(parents=True, exist_ok=True)

    grouped_audio: dict[str, list[dict[str, Any]]] = defaultdict(list)
    grouped_model: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped_audio[record.get("file_id", "unknown")].append(record)
        grouped_model[_model_key(record)].append(record)

    audio_files = []
    for file_id, file_records in sorted(grouped_audio.items()):
        file_path = by_audio_dir / f"{safe_name(file_id, 120)}.md"
        file_path.write_text(_audio_markdown(file_id, file_records), encoding="utf-8")
        audio_files.append(file_path)

    model_files = []
    for model_key, model_records in sorted(grouped_model.items()):
        model_path = by_model_dir / f"{safe_name(model_key, 120)}.md"
        model_path.write_text(_model_markdown(model_key, model_records), encoding="utf-8")
        model_files.append(model_path)

    (output_dir / "index.md").write_text(
        _index_markdown(grouped_audio, grouped_model),
        encoding="utf-8",
    )
    return {
        "records": len(records),
        "audio_files": len(audio_files),
        "model_files": len(model_files),
        "output_dir": str(output_dir),
    }


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def _audio_markdown(file_id: str, records: list[dict[str, Any]]) -> str:
    records = sorted(records, key=lambda row: (_model_key(row), row.get("status", "")))
    title = _display_file_name(records[0]) if records else file_id
    lines = [
        f"# {title}",
        "",
        f"- File ID: `{file_id}`",
        f"- Path: `{records[0].get('file_path', '') if records else ''}`",
        "",
        "## Model Summary",
        "",
        "| Model | Status | Transcript | Tags | Emotion | Error |",
        "| --- | --- | ---: | ---: | --- | --- |",
    ]
    for record in records:
        transcript = _transcript(record)
        tag_count = len(record.get("nonverbal_tags", [])) + len(record.get("noise_background_tags", []))
        emotion = ", ".join(_emotion_labels(record)) or ""
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(_model_key(record)),
                    _cell(record.get("status", "")),
                    str(len(transcript)),
                    str(tag_count),
                    _cell(emotion),
                    _cell(_short_error(record.get("error"))),
                ]
            )
            + " |"
        )
    lines.append("")
    for record in records:
        lines.extend(_record_markdown(record))
    return "\n".join(lines).rstrip() + "\n"


def _model_markdown(model_key: str, records: list[dict[str, Any]]) -> str:
    records = sorted(records, key=lambda row: row.get("file_id", ""))
    lines = [
        f"# {model_key}",
        "",
        "| Audio | Status | Transcript chars | Tags | Emotion |",
        "| --- | --- | ---: | ---: | --- |",
    ]
    for record in records:
        tag_count = len(record.get("nonverbal_tags", [])) + len(record.get("noise_background_tags", []))
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(_display_file_name(record)),
                    _cell(record.get("status", "")),
                    str(len(_transcript(record))),
                    str(tag_count),
                    _cell(", ".join(_emotion_labels(record)) or ""),
                ]
            )
            + " |"
        )
    lines.append("")
    for record in records:
        lines.extend(
            [
                f"## {_display_file_name(record)}",
                "",
                f"- File ID: `{record.get('file_id', '')}`",
                f"- Status: `{record.get('status', '')}`",
                "",
            ]
        )
        lines.extend(_text_and_tags_markdown(record, heading_level="###"))
    return "\n".join(lines).rstrip() + "\n"


def _index_markdown(
    grouped_audio: dict[str, list[dict[str, Any]]],
    grouped_model: dict[str, list[dict[str, Any]]],
) -> str:
    lines = [
        "# Readable Audio Benchmark Outputs",
        "",
        "Open `by_audio` to compare all models for one audio clip, or `by_model` to scan one model across all clips.",
        "",
        "## By Audio",
        "",
    ]
    for file_id, records in sorted(grouped_audio.items()):
        title = _display_file_name(records[0]) if records else file_id
        rel = Path("by_audio") / f"{safe_name(file_id, 120)}.md"
        lines.append(f"- [{_escape_link_text(title)}]({rel.as_posix()})")
    lines.extend(["", "## By Model", ""])
    for model_key in sorted(grouped_model):
        rel = Path("by_model") / f"{safe_name(model_key, 120)}.md"
        lines.append(f"- [{_escape_link_text(model_key)}]({rel.as_posix()})")
    return "\n".join(lines).rstrip() + "\n"


def _record_markdown(record: dict[str, Any]) -> list[str]:
    lines = [
        f"## {_model_key(record)}",
        "",
        f"- Status: `{record.get('status', '')}`",
        f"- Raw response: `{record.get('raw_response_path', '')}`",
    ]
    if record.get("error"):
        lines.extend(["", "Error:", "", _fence(str(record["error"]))])
    lines.append("")
    lines.extend(_text_and_tags_markdown(record, heading_level="###"))
    return lines


def _text_and_tags_markdown(record: dict[str, Any], heading_level: str) -> list[str]:
    transcription = record.get("transcription") or {}
    segments = transcription.get("segments") or []
    words = transcription.get("words") or []
    lines = [
        f"{heading_level} Transcript",
        "",
        _fence(transcription.get("transcript") or ""),
        "",
        f"{heading_level} Tagged Transcript",
        "",
        _fence(record.get("tagged_transcript") or ""),
        "",
        f"{heading_level} Segments",
        "",
    ]
    if segments:
        for index, segment in enumerate(segments, start=1):
            if isinstance(segment, dict):
                text = segment.get("text") or segment.get("transcript") or ""
                start = segment.get("start") or segment.get("start_time") or ""
                end = segment.get("end") or segment.get("end_time") or ""
                lines.append(f"{index}. `{start}`-`{end}` {_plain(text)}")
            else:
                lines.append(f"{index}. {_plain(segment)}")
    else:
        lines.append("_No provider segments returned._")
    lines.extend(
        [
            "",
            f"{heading_level} Tags",
            "",
            _tag_table("Non-verbal", record.get("nonverbal_tags") or []),
            "",
            _tag_table("Background / noise", record.get("noise_background_tags") or []),
            "",
            _emotion_table(record.get("emotion_tags") or []),
            "",
            f"{heading_level} Metadata",
            "",
            f"- Language: `{transcription.get('language', '')}`",
            f"- Word timestamps available: `{transcription.get('word_timestamp_available', False)}`",
            f"- Word count returned: `{len(words)}`",
            f"- Quality: `{json.dumps(record.get('quality') or {}, ensure_ascii=False)}`",
            f"- Reliability: `{json.dumps(record.get('reliability') or {}, ensure_ascii=False)}`",
            "",
        ]
    )
    return lines


def _tag_table(title: str, tags: list[dict[str, Any]]) -> str:
    if not tags:
        return f"**{title}:** none"
    lines = [
        f"**{title}:**",
        "",
        "| Label | Raw label | Confidence | Time | Evidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for tag in tags:
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(tag.get("label", "")),
                    _cell(tag.get("raw_label", "")),
                    _cell(tag.get("confidence", "")),
                    _cell(tag.get("time_status", "")),
                    _cell(tag.get("evidence", "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _emotion_table(tags: list[dict[str, Any]]) -> str:
    if not tags:
        return "**Emotion:** none"
    lines = [
        "**Emotion:**",
        "",
        "| Label | Confidence | Scope | Evidence |",
        "| --- | --- | --- | --- |",
    ]
    for tag in tags:
        lines.append(
            "| "
            + " | ".join(
                [
                    _cell(tag.get("label", "")),
                    _cell(tag.get("confidence", "")),
                    _cell(tag.get("scope", "")),
                    _cell(tag.get("evidence", "")),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def _model_key(record: dict[str, Any]) -> str:
    return f"{record.get('provider', '')}_{record.get('model', '')}"


def _transcript(record: dict[str, Any]) -> str:
    return str((record.get("transcription") or {}).get("transcript") or "")


def _emotion_labels(record: dict[str, Any]) -> list[str]:
    labels = []
    for tag in record.get("emotion_tags") or []:
        if isinstance(tag, dict) and tag.get("label"):
            labels.append(str(tag["label"]))
    return labels


def _display_file_name(record: dict[str, Any]) -> str:
    path = record.get("file_path") or ""
    return Path(path).name if path else record.get("file_id", "unknown")


def _short_error(error: Any) -> str:
    if not error:
        return ""
    text = str(error)
    return text[:117] + "..." if len(text) > 120 else text


def _cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _plain(value: Any) -> str:
    return str(value).replace("\n", " ").strip()


def _fence(text: str) -> str:
    return "```text\n" + str(text).replace("```", "'''") + "\n```"


def _escape_link_text(text: str) -> str:
    return text.replace("[", "\\[").replace("]", "\\]")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate human-readable text+tag benchmark outputs.")
    parser.add_argument(
        "--input",
        default="audio_benchmark/outputs/normalized/audio_context_results.jsonl",
        help="Normalized JSONL results path.",
    )
    parser.add_argument(
        "--output_dir",
        default="audio_benchmark/outputs/readable",
        help="Readable Markdown output directory.",
    )
    args = parser.parse_args()
    summary = generate_readable_outputs(Path(args.input), Path(args.output_dir))
    print(
        "Generated readable outputs: "
        f"{summary['records']} records, "
        f"{summary['audio_files']} audio files, "
        f"{summary['model_files']} model files -> {summary['output_dir']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


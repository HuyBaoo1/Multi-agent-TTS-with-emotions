from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from audio_benchmark.schemas import EMOTION_LABELS


def main() -> int:
    parser = argparse.ArgumentParser(description="Score model emotion tags against reviewed ground truth.")
    parser.add_argument("--results", default="audio_benchmark/outputs/normalized/audio_context_results.jsonl")
    parser.add_argument("--ground_truth_dir", default="ground_truth/by_audio")
    parser.add_argument("--output_dir", default="audio_benchmark/outputs/reports")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    records = load_results(Path(args.results))
    ground_truth, issues = load_reviewed_ground_truth(Path(args.ground_truth_dir))
    details, metrics = score_emotions(records, ground_truth)

    write_csv(output_dir / "emotion_groundtruth_details.csv", details)
    write_csv(output_dir / "emotion_groundtruth_metrics.csv", metrics)
    write_csv(output_dir / "emotion_groundtruth_issues.csv", issues)
    write_markdown(output_dir / "emotion_groundtruth_report.md", metrics, details, issues, len(ground_truth))

    print(f"reviewed_valid_ground_truth={len(ground_truth)}")
    print(f"issues={len(issues)}")
    print(output_dir / "emotion_groundtruth_metrics.csv")
    print(output_dir / "emotion_groundtruth_details.csv")
    print(output_dir / "emotion_groundtruth_issues.csv")
    print(output_dir / "emotion_groundtruth_report.md")
    return 0


def load_results(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_reviewed_ground_truth(ground_truth_dir: Path) -> tuple[dict[str, set[str]], list[dict[str, str]]]:
    ground_truth: dict[str, set[str]] = {}
    issues: list[dict[str, str]] = []
    for path in sorted(ground_truth_dir.glob("*.csv")):
        if path.name == "index.csv":
            continue
        rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
        if not rows:
            continue
        row = rows[0]
        if (row.get("review_status") or "").strip().lower() != "reviewed":
            continue
        file_id = row.get("file_id", "")
        raw = (row.get("emotion_tags_json") or "").strip()
        if not raw:
            issues.append(issue(path, file_id, "empty_emotion_tags_json", "Reviewed row has no emotion JSON."))
            continue
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError as exc:
            issues.append(issue(path, file_id, "invalid_json", str(exc)))
            continue
        if not isinstance(parsed, list):
            issues.append(issue(path, file_id, "not_json_array", "emotion_tags_json must be a JSON array."))
            continue
        labels = set()
        invalid_labels = []
        for item in parsed:
            if not isinstance(item, dict):
                issues.append(issue(path, file_id, "invalid_item", "Each emotion item must be an object."))
                continue
            label = str(item.get("label", "")).strip()
            if label not in EMOTION_LABELS:
                invalid_labels.append(label)
            else:
                labels.add(label)
        if invalid_labels:
            issues.append(
                issue(
                    path,
                    file_id,
                    "invalid_label",
                    "Invalid emotion labels: " + ", ".join(sorted(set(invalid_labels))),
                )
            )
            continue
        if not labels:
            issues.append(issue(path, file_id, "no_valid_labels", "Reviewed row has no valid emotion labels."))
            continue
        ground_truth[file_id] = labels
    return ground_truth, issues


def score_emotions(
    records: list[dict[str, Any]],
    ground_truth: dict[str, set[str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    details = []
    model_stats: dict[tuple[str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "files": 0,
            "exact": 0,
            "overlap": 0,
            "tp": 0,
            "fp": 0,
            "fn": 0,
            "predicted_any": 0,
            "errors": 0,
        }
    )

    for record in records:
        file_id = record.get("file_id", "")
        if file_id not in ground_truth:
            continue
        provider = record.get("provider", "")
        model = record.get("model", "")
        key = (provider, model)
        gt_labels = ground_truth[file_id]
        pred_labels = predicted_emotions(record)
        tp = len(gt_labels & pred_labels)
        fp = len(pred_labels - gt_labels)
        fn = len(gt_labels - pred_labels)
        exact = pred_labels == gt_labels
        overlap = bool(gt_labels & pred_labels)

        stats = model_stats[key]
        stats["files"] += 1
        stats["exact"] += int(exact)
        stats["overlap"] += int(overlap)
        stats["tp"] += tp
        stats["fp"] += fp
        stats["fn"] += fn
        stats["predicted_any"] += int(bool(pred_labels))
        stats["errors"] += int(record.get("status") == "error")

        details.append(
            {
                "file_id": file_id,
                "provider": provider,
                "model": model,
                "status": record.get("status", ""),
                "ground_truth_labels": labels_to_text(gt_labels),
                "predicted_labels": labels_to_text(pred_labels),
                "exact_match": exact,
                "any_overlap": overlap,
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "error": record.get("error") or "",
            }
        )

    metrics = []
    for (provider, model), stats in sorted(model_stats.items()):
        precision = safe_div(stats["tp"], stats["tp"] + stats["fp"])
        recall = safe_div(stats["tp"], stats["tp"] + stats["fn"])
        f1 = safe_div(2 * precision * recall, precision + recall)
        files = stats["files"]
        metrics.append(
            {
                "provider": provider,
                "model": model,
                "ground_truth_files": files,
                "exact_match_rate": safe_div(stats["exact"], files),
                "any_overlap_rate": safe_div(stats["overlap"], files),
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "predicted_emotion_coverage": safe_div(stats["predicted_any"], files),
                "error_rate_on_gt_files": safe_div(stats["errors"], files),
                "tp": stats["tp"],
                "fp": stats["fp"],
                "fn": stats["fn"],
            }
        )
    metrics.sort(key=lambda row: (row["f1"], row["exact_match_rate"], -row["error_rate_on_gt_files"]), reverse=True)
    return details, metrics


def predicted_emotions(record: dict[str, Any]) -> set[str]:
    if record.get("status") != "success":
        return set()
    labels = set()
    for tag in record.get("emotion_tags") or []:
        if not isinstance(tag, dict):
            continue
        label = str(tag.get("label", "")).strip()
        if label in EMOTION_LABELS:
            labels.add(label)
    return labels


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_markdown(
    path: Path,
    metrics: list[dict[str, Any]],
    details: list[dict[str, Any]],
    issues: list[dict[str, str]],
    gt_count: int,
) -> None:
    lines = [
        "# Emotion Ground Truth Report",
        "",
        f"Reviewed valid ground-truth files used: {gt_count}",
        "",
        "## Metrics",
        "",
    ]
    lines.extend(markdown_table(metrics))
    lines.extend(["", "## Annotation Issues", ""])
    if issues:
        lines.extend(markdown_table(issues))
    else:
        lines.append("No annotation issues found.")
    lines.extend(["", "## Per-File Details", ""])
    lines.extend(markdown_table(details))
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def markdown_table(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return ["No rows."]
    headers = list(rows[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(format_cell(row.get(header, "")) for header in headers) + " |")
    return lines


def format_cell(value: Any) -> str:
    if isinstance(value, float):
        value = round(value, 4)
    return str(value).replace("|", "\\|").replace("\n", " ")


def labels_to_text(labels: set[str]) -> str:
    return ";".join(sorted(labels))


def safe_div(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0.0


def issue(path: Path, file_id: str, issue_type: str, message: str) -> dict[str, str]:
    return {
        "file": str(path),
        "file_id": file_id,
        "issue": issue_type,
        "message": message,
    }


if __name__ == "__main__":
    raise SystemExit(main())

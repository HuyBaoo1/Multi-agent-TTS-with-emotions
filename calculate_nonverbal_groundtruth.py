from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from audio_benchmark.schemas import NONVERBAL_LABELS


def main() -> int:
    parser = argparse.ArgumentParser(description="Score nonverbal/background tags against ground truth.")
    parser.add_argument("--results", default="audio_benchmark/outputs/normalized/audio_context_results.jsonl")
    parser.add_argument("--ground_truth_dir", default="ground_truth/by_audio")
    parser.add_argument("--output_dir", default="audio_benchmark/outputs/reports")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    records = load_results(Path(args.results))
    ground_truth, issues = load_ground_truth(Path(args.ground_truth_dir))
    details, metrics = score_records(records, ground_truth)

    write_csv(output_dir / "nonverbal_groundtruth_details.csv", details)
    write_csv(output_dir / "nonverbal_groundtruth_metrics.csv", metrics)
    write_csv(output_dir / "nonverbal_groundtruth_issues.csv", issues)
    write_markdown(output_dir / "nonverbal_groundtruth_report.md", metrics, details, issues, len(ground_truth))

    print(f"valid_ground_truth_files={len(ground_truth)}")
    print(f"issues={len(issues)}")
    print(output_dir / "nonverbal_groundtruth_metrics.csv")
    print(output_dir / "nonverbal_groundtruth_details.csv")
    print(output_dir / "nonverbal_groundtruth_issues.csv")
    print(output_dir / "nonverbal_groundtruth_report.md")
    return 0


def load_results(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def load_ground_truth(ground_truth_dir: Path) -> tuple[dict[str, dict[str, set[str]]], list[dict[str, str]]]:
    ground_truth: dict[str, dict[str, set[str]]] = {}
    issues: list[dict[str, str]] = []
    for path in sorted(ground_truth_dir.glob("*.csv")):
        if path.name == "index.csv":
            continue
        rows = list(csv.DictReader(path.open(encoding="utf-8-sig", newline="")))
        if not rows:
            continue
        row = rows[0]
        file_id = row.get("file_id", "")
        review_status = (row.get("review_status") or "").strip().lower()
        nonverbal_raw = (row.get("nonverbal_tags_json") or "").strip()
        background_raw = (row.get("background_tags_json") or "").strip()
        has_annotation = review_status == "reviewed" or nonverbal_raw not in {"", "[]"} or background_raw not in {"", "[]"}
        if not has_annotation:
            continue

        nonverbal_labels, nonverbal_issues = parse_tag_labels(path, file_id, "nonverbal_tags_json", nonverbal_raw)
        background_labels, background_issues = parse_tag_labels(path, file_id, "background_tags_json", background_raw)
        issues.extend(nonverbal_issues)
        issues.extend(background_issues)
        if nonverbal_issues or background_issues:
            continue

        ground_truth[file_id] = {
            "nonverbal": nonverbal_labels,
            "background": background_labels,
            "combined": nonverbal_labels | background_labels,
        }
    return ground_truth, issues


def parse_tag_labels(path: Path, file_id: str, field: str, raw: str) -> tuple[set[str], list[dict[str, str]]]:
    issues: list[dict[str, str]] = []
    raw = raw or "[]"
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return set(), [issue(path, file_id, field, "invalid_json", str(exc))]
    if not isinstance(parsed, list):
        return set(), [issue(path, file_id, field, "not_json_array", f"{field} must be a JSON array.")]

    labels = set()
    invalid_labels = []
    invalid_items = 0
    for item in parsed:
        if not isinstance(item, dict):
            invalid_items += 1
            continue
        label = str(item.get("label", "")).strip()
        if label not in NONVERBAL_LABELS:
            invalid_labels.append(label)
        else:
            labels.add(label)
    if invalid_items:
        issues.append(issue(path, file_id, field, "invalid_item", "Each tag item must be an object."))
    if invalid_labels:
        issues.append(
            issue(
                path,
                file_id,
                field,
                "invalid_label",
                "Invalid labels: " + ", ".join(sorted(set(invalid_labels))),
            )
        )
    return labels, issues


def score_records(
    records: list[dict[str, Any]],
    ground_truth: dict[str, dict[str, set[str]]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    details = []
    stats: dict[tuple[str, str], dict[str, Any]] = defaultdict(make_stats)

    for record in records:
        file_id = record.get("file_id", "")
        if file_id not in ground_truth:
            continue
        provider = record.get("provider", "")
        model = record.get("model", "")
        key = (provider, model)
        predicted = predicted_labels(record)
        current = stats[key]
        current["files"] += 1
        current["errors"] += int(record.get("status") == "error")

        row = {
            "file_id": file_id,
            "provider": provider,
            "model": model,
            "status": record.get("status", ""),
            "error": record.get("error") or "",
        }
        for group in ("nonverbal", "background", "combined"):
            gt_labels = ground_truth[file_id][group]
            pred_labels = predicted[group]
            tp = len(gt_labels & pred_labels)
            fp = len(pred_labels - gt_labels)
            fn = len(gt_labels - pred_labels)
            exact = pred_labels == gt_labels
            overlap = bool(gt_labels & pred_labels)
            current[group]["tp"] += tp
            current[group]["fp"] += fp
            current[group]["fn"] += fn
            current[group]["exact"] += int(exact)
            current[group]["overlap"] += int(overlap)
            current[group]["predicted_any"] += int(bool(pred_labels))
            row[f"{group}_ground_truth_labels"] = labels_to_text(gt_labels)
            row[f"{group}_predicted_labels"] = labels_to_text(pred_labels)
            row[f"{group}_exact_match"] = exact
            row[f"{group}_any_overlap"] = overlap
            row[f"{group}_tp"] = tp
            row[f"{group}_fp"] = fp
            row[f"{group}_fn"] = fn
        details.append(row)

    metrics = []
    for (provider, model), model_stats in sorted(stats.items()):
        files = model_stats["files"]
        metric_row: dict[str, Any] = {
            "provider": provider,
            "model": model,
            "ground_truth_files": files,
            "error_rate_on_gt_files": safe_div(model_stats["errors"], files),
        }
        for group in ("nonverbal", "background", "combined"):
            group_stats = model_stats[group]
            precision = safe_div(group_stats["tp"], group_stats["tp"] + group_stats["fp"])
            recall = safe_div(group_stats["tp"], group_stats["tp"] + group_stats["fn"])
            f1 = safe_div(2 * precision * recall, precision + recall)
            metric_row[f"{group}_precision"] = precision
            metric_row[f"{group}_recall"] = recall
            metric_row[f"{group}_f1"] = f1
            metric_row[f"{group}_exact_match_rate"] = safe_div(group_stats["exact"], files)
            metric_row[f"{group}_overlap_rate"] = safe_div(group_stats["overlap"], files)
            metric_row[f"{group}_predicted_coverage"] = safe_div(group_stats["predicted_any"], files)
            metric_row[f"{group}_tp"] = group_stats["tp"]
            metric_row[f"{group}_fp"] = group_stats["fp"]
            metric_row[f"{group}_fn"] = group_stats["fn"]
        metrics.append(metric_row)

    metrics.sort(
        key=lambda row: (
            row["combined_f1"],
            row["background_f1"],
            row["nonverbal_f1"],
            -row["error_rate_on_gt_files"],
        ),
        reverse=True,
    )
    return details, metrics


def make_stats() -> dict[str, Any]:
    return {
        "files": 0,
        "errors": 0,
        "nonverbal": make_group_stats(),
        "background": make_group_stats(),
        "combined": make_group_stats(),
    }


def make_group_stats() -> dict[str, int]:
    return {
        "tp": 0,
        "fp": 0,
        "fn": 0,
        "exact": 0,
        "overlap": 0,
        "predicted_any": 0,
    }


def predicted_labels(record: dict[str, Any]) -> dict[str, set[str]]:
    if record.get("status") != "success":
        return {"nonverbal": set(), "background": set(), "combined": set()}
    nonverbal = {
        str(tag.get("label", "")).strip()
        for tag in record.get("nonverbal_tags") or []
        if isinstance(tag, dict) and str(tag.get("label", "")).strip() in NONVERBAL_LABELS
    }
    background = {
        str(tag.get("label", "")).strip()
        for tag in record.get("noise_background_tags") or []
        if isinstance(tag, dict) and str(tag.get("label", "")).strip() in NONVERBAL_LABELS
    }
    return {"nonverbal": nonverbal, "background": background, "combined": nonverbal | background}


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
        "# Nonverbal And Background Ground Truth Report",
        "",
        f"Valid ground-truth files used: {gt_count}",
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


def issue(path: Path, file_id: str, field: str, issue_type: str, message: str) -> dict[str, str]:
    return {
        "file": str(path),
        "file_id": file_id,
        "field": field,
        "issue": issue_type,
        "message": message,
    }


if __name__ == "__main__":
    raise SystemExit(main())


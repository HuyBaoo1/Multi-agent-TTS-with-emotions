from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


CSV_FILES = {
    "model_comparison": "model_comparison.csv",
    "transcription_metrics": "transcription_metrics.csv",
    "nonverbal_metrics": "nonverbal_metrics.csv",
    "emotion_metrics": "emotion_metrics.csv",
    "reliability_summary": "reliability_summary.csv",
    "error_report": "error_report.csv",
}


def write_reports(metrics: dict[str, list[dict[str, Any]]], reports_dir: Path) -> None:
    reports_dir.mkdir(parents=True, exist_ok=True)
    for metric_name, filename in CSV_FILES.items():
        _write_csv(reports_dir / filename, metrics.get(metric_name, []))
    _write_markdown_report(metrics, reports_dir / "benchmark_report.md")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_markdown_report(metrics: dict[str, list[dict[str, Any]]], path: Path) -> None:
    lines = [
        "# Audio Understanding Benchmark Report",
        "",
        "This report compares one-pass audio context extraction across selected providers and models.",
        "",
        "## Reliability Summary",
        "",
    ]
    reliability = metrics.get("reliability_summary", [])
    if reliability:
        lines.extend(_markdown_table(reliability))
    else:
        lines.append("No reliability rows were generated.")
    lines.extend(["", "## Model Comparison", ""])
    comparison = metrics.get("model_comparison", [])
    if comparison:
        lines.extend(_markdown_table(comparison))
    else:
        lines.append("No model comparison rows were generated.")
    errors = metrics.get("error_report", [])
    lines.extend(["", "## Errors And Skips", ""])
    if errors:
        lines.extend(_markdown_table(errors[:50]))
        if len(errors) > 50:
            lines.append("")
            lines.append(f"Showing first 50 of {len(errors)} rows. See error_report.csv for all rows.")
    else:
        lines.append("No errors or skipped calls were recorded.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _markdown_table(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return []
    headers = list(rows[0].keys())
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        values = [_format_cell(row.get(header, "")) for header in headers]
        lines.append("| " + " | ".join(values) + " |")
    return lines


def _format_cell(value: Any) -> str:
    if isinstance(value, float):
        value = round(value, 4)
    return str(value).replace("|", "\\|").replace("\n", " ")


# Audio Understanding Benchmark

One-pass benchmark pipeline for comparing Gemini, OpenAI, and ElevenLabs on the same audio files.

The benchmark extracts:

- transcript / STT
- non-verbal and background tags
- emotion tags
- tagged transcript when supported
- reliability and agreement reports

It does not split audio into windows and does not implement sliding-window localization. Each selected provider/model is called at most once per audio file unless you intentionally bypass cache with `--force_refresh true`.

## Setup

```bash
pip install -r requirements.txt
copy .env.example .env
```

Fill `.env` with the keys for providers you want to run:

```text
GEMINI_API_KEY=
OPENAI_API_KEY=
ELEVENLABS_API_KEY=
```

The CLI prints only whether each key exists, never the key value.

## Dry Run

```bash
python run_audio_benchmark.py --audio_dir audio/Audio-short --output_dir audio_benchmark/outputs --dry_run
```

## Sample Run

```bash
python run_audio_benchmark.py --audio_dir audio/Audio-short --output_dir audio_benchmark/outputs --limit 3
```

## Full Run

```bash
python run_audio_benchmark.py --audio_dir audio/Audio-short --output_dir audio_benchmark/outputs
```

## Useful Options

```bash
--providers gemini,openai,elevenlabs
--models gemini-3.5-flash,gemini-3.1-pro-preview,gpt-4o-mini-transcribe,scribe_v2
--limit 10
--dry_run
--force_refresh false
--ground_truth path/to/ground_truth.csv
```

Ground truth can be JSON or CSV. Use one of `file_id`, `file_path`, or `file_name` plus a `transcript` field.

## Outputs

```text
audio_benchmark/outputs/
  raw/
    <provider>_<model>_<file_id>.json
  normalized/
    audio_context_results.jsonl
  reports/
    model_comparison.csv
    transcription_metrics.csv
    nonverbal_metrics.csv
    emotion_metrics.csv
    reliability_summary.csv
    error_report.csv
    benchmark_report.md
```

## Provider Notes

- Gemini uses the strict JSON audio context prompt and can return transcript, tags, emotions, and reliability if the model supports audio input.
- OpenAI transcription is treated as STT-only. Non-verbal and emotion fields remain empty instead of being inferred.
- ElevenLabs Scribe is treated as STT plus available word timestamps, diarization, and audio event tags. Emotion is left empty or `not_applicable` when no speech is present.

## Benchmark Run: audio/Audio-short

Dataset: 10 files in `audio/Audio-short`.
Last cached rerun: 2026-06-26, 40 cached tasks, 0 new API calls, 0 skipped tasks.

Command used:

```bash
python run_audio_benchmark.py --audio_dir audio/Audio-short --output_dir audio_benchmark/outputs --providers gemini,openai,elevenlabs --models gemini-3.5-flash,gemini-3.1-pro-preview,gpt-4o-mini-transcribe,scribe_v2 --force_refresh false
```

### Quick Verdict

| Use case | Best current choice | Why |
| --- | --- | --- |
| Transcript + timestamped non-verbal/background tags | ElevenLabs `scribe_v2` | 10/10 success, non-empty transcripts, 41 timestamped tags. |
| Emotion/context extraction | Gemini `gemini-3.5-flash` on labeled subset | Best emotion F1 so far, but only 4 valid ground-truth files. |
| Balanced context with model confidence | Gemini `gemini-3.1-pro-preview` | Highest custom trust score before ground-truth scoring. |
| OpenAI transcription | Not evaluated | All OpenAI calls failed with `insufficient_quota`. |

### Model Snapshot

| Model | Success | Errors | Avg tags/file | Emotion output | Reliability score |
| --- | ---: | ---: | ---: | --- | ---: |
| `scribe_v2` | 10/10 | 0/10 | 4.10 | none returned | 65.0 |
| `gemini-3.1-pro-preview` | 9/10 | 1/10 | 0.50 | returned | 53.5 |
| `gemini-3.5-flash` | 9/10 | 1/10 | 0.30 | returned | 50.5 |
| `gpt-4o-mini-transcribe` | 0/10 | 10/10 | 0.00 | none | -35.0 |

### Emotion Ground Truth

Emotion scoring used `4` reviewed, valid ground-truth files. Two reviewed files were excluded: one has invalid JSON, and one uses the non-taxonomy label `confused`.

| Rank | Model | Exact match | Overlap | Precision | Recall | F1 |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 1 | `gemini-3.5-flash` | 0.25 | 0.25 | 0.333 | 0.25 | 0.286 |
| 2 | `gemini-3.1-pro-preview` | 0.00 | 0.25 | 0.250 | 0.25 | 0.250 |
| 3 | `scribe_v2` | 0.00 | 0.00 | 0.000 | 0.00 | 0.000 |
| 4 | `gpt-4o-mini-transcribe` | 0.00 | 0.00 | 0.000 | 0.00 | 0.000 |

Interpretation: Gemini is the only provider currently returning emotion labels in this pipeline. The labeled subset is still small, so treat the ranking as a checkpoint, not a final conclusion.

### Known Limits

- No transcript ground truth yet, so WER/CER are not available.
- Both Gemini models still have 1 failed audio because the response was not parseable JSON.
- OpenAI cannot be judged until quota is available.
- Emotion ground truth should be expanded and reviewed before relying on the F1 ranking.

### Key Outputs

```text
audio_benchmark/outputs/readable/index.md
audio_benchmark/outputs/normalized/audio_context_results.jsonl
audio_benchmark/outputs/reports/reliability_summary.csv
audio_benchmark/outputs/reports/emotion_groundtruth_metrics.csv
audio_benchmark/outputs/reports/emotion_groundtruth_issues.csv
audio_benchmark/outputs/reports/benchmark_report.md
```

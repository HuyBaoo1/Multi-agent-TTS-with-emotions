# Audio Understanding Benchmark

One-pass benchmark pipeline for comparing Gemini, OpenAI, and ElevenLabs on the same audio files.

The benchmark extracts:

- transcript / STT
- non-verbal and background tags
- emotion tags
- tagged transcript when supported
- reliability and agreement reports



```

## Full Run

```bash
python run_audio_benchmark.py --audio_dir audio/Audio-short --output_dir audio_benchmark/outputs
```

Ground truth can be JSON or CSV. Use one of `file_id`, `file_path`, or `file_name` plus a `transcript` field.



The normalized benchmark file contains 40 rows: 10 audio files x 4 model targets.

### Model Comparison

| Provider | Model | Files | Success | Errors | Coverage | Empty transcript rate | Avg tags/file |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ElevenLabs | scribe_v2 | 10 | 10 | 0 | 1.00 | 0.00 | 4.10 |
| Gemini | gemini-3.1-pro-preview | 10 | 9 | 1 | 0.90 | 0.10 | 0.50 |
| Gemini | gemini-3.5-flash | 10 | 9 | 1 | 0.90 | 0.10 | 0.30 |
| OpenAI | gpt-4o-mini-transcribe | 10 | 0 | 10 | 0.00 | 1.00 | 0.00 |

### Transcription Metrics

| Provider | Model | Coverage | Empty transcript rate | Avg peer transcript similarity |
| --- | --- | ---: | ---: | ---: |
| ElevenLabs | scribe_v2 | 1.00 | 0.00 | 0.4494 |
| Gemini | gemini-3.1-pro-preview | 0.90 | 0.10 | 0.5570 |
| Gemini | gemini-3.5-flash | 0.90 | 0.10 | 0.5532 |
| OpenAI | gpt-4o-mini-transcribe | 0.00 | 1.00 | 0.0667 |

### Non-Verbal And Background Tags

| Provider | Model | Avg tags/file | Global tags | Timestamped tags | Peer Jaccard | Nonverbal F1 | Background F1 | Combined F1|
| --- | --- | ---: | ---: | ---: | ---: |
| ElevenLabs | scribe_v2 | 4.10 | 0 | 41 | 0.0444 | 0.250 | 0.200 | 0.357
| Gemini | gemini-3.1-pro-preview | 0.50 | 5 | 0 | 0.4778 | 0.000 | 0.250 | 0.174 |
| Gemini | gemini-3.5-flash | 0.30 | 1 | 2 | 0.5000 | 0.000 | 0.154 | 0.100 | 
| OpenAI | gpt-4o-mini-transcribe | 0.00 | 0 | 0 | 0.5333 | 0.000 | 0.000 | 0.000|

ElevenLabs produced the richest non-speech output in this run, including timestamped audio-event tags. Gemini produced fewer tags, mostly global tags. OpenAI was not evaluated for tags because all OpenAI calls failed due quota.

### Emotion Metrics

| Provider | Model | Emotion labels observed | Peer emotion agreement | uncertain_emotion rate | not_applicable rate |
| --- | --- | --- | ---: | ---: | ---: |
| ElevenLabs | scribe_v2 | none returned | 0.3333 | 0.00 | 0.00 |
| Gemini | gemini-3.1-pro-preview | calm, neutral, happy, excited, not_applicable | 0.2667 | 0.00 | 0.10 |
| Gemini | gemini-3.5-flash | calm, excited, happy, not_applicable | 0.2667 | 0.00 | 0.10 |
| OpenAI | gpt-4o-mini-transcribe | none returned | 0.3333 | 0.00 | 0.00 |


### Reliability Summary

| Rank | Provider | Model | Reliability score |
| ---: | --- | --- | ---: |
| 1 | ElevenLabs | scribe_v2 | 65.0 |
| 2 | Gemini | gemini-3.1-pro-preview | 53.5 |
| 3 | Gemini | gemini-3.5-flash | 50.5 |
| 4 | OpenAI | gpt-4o-mini-transcribe | -35.0 |

The reliability score favors coverage, non-empty transcripts, useful non-verbal tags, and cross-model emotion agreement, while penalizing API errors and unsupported fields.

### Evaluation

Best overall in this run: ElevenLabs `scribe_v2`. It completed all 10 files, returned non-empty transcripts for all files, and produced 41 timestamped non-verbal/background tags.

Best emotion coverage: Gemini. Both Gemini models returned emotion labels for most successful files, while ElevenLabs and OpenAI did not provide emotion tags through this pipeline.

Most reliable Gemini model in this run: `gemini-3.1-pro-preview`, with a slightly higher reliability score and more detected tags than `gemini-3.5-flash`.

OpenAI result is not a quality judgment. All 10 OpenAI calls failed with `insufficient_quota`, so `gpt-4o-mini-transcribe` could not be evaluated on this dataset.

Known issues from this run:

- Both Gemini models failed on one audio file because the response was not parseable JSON.
- Non-verbal tag agreement is low because providers expose different capabilities and tag granularity.
- Emotion agreement should not be treated as accuracy without labeled emotion ground truth.

Report files:

```text
audio_benchmark/outputs/normalized/audio_context_results.jsonl
audio_benchmark/outputs/reports/model_comparison.csv
audio_benchmark/outputs/reports/transcription_metrics.csv
audio_benchmark/outputs/reports/nonverbal_metrics.csv
audio_benchmark/outputs/reports/emotion_metrics.csv
audio_benchmark/outputs/reports/reliability_summary.csv
audio_benchmark/outputs/reports/error_report.csv
audio_benchmark/outputs/reports/benchmark_report.md
```

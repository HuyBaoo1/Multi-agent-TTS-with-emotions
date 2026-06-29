# Ground Truth Annotation

Use this folder to create human-labeled ground truth for evaluating model accuracy.

For a serious benchmark, yes: you should label transcript, non-verbal/background tags, and emotion. Without this, the current reports can compare model agreement and coverage, but they cannot tell which model is truly correct.

## Files

```text
ground_truth/
  audio_short_ground_truth_template.csv
  README.md
  schema.md
```

`audio_short_ground_truth_template.csv` is pre-filled with the 10 audio files from `audio/Audio-short`.

## Recommended Workflow

1. Listen to each audio file once or twice.
2. Fill `ground_truth_transcript` with the best human transcript.
3. Fill `ground_truth_tagged_transcript` only when inline tag placement is clear.
4. Fill tag columns as JSON arrays.
5. Fill emotion only if speech or human vocal sound is present.
6. Set `review_status` to `reviewed` after a second pass.

For higher reliability, use two annotators and resolve disagreements into a final reviewed file.

## Example Tag JSON

```json
[
  {
    "label": "laughter",
    "evidence": "audible laugh after the sentence",
    "time_status": "global"
  }
]
```

If timing is clear from a media player, use:

```json
[
  {
    "label": "music",
    "evidence": "background music starts near the end",
    "time_status": "timestamped",
    "start": 18.2,
    "end": 22.0
  }
]
```

If the exact time is not clear, keep `time_status` as `global`.

## Example Emotion JSON

```json
[
  {
    "label": "happy",
    "evidence": "speaker sounds cheerful",
    "scope": "whole_audio"
  }
]
```

Use `uncertain_emotion` when the emotion is unclear. Use `not_applicable` when there is no speech or human vocal sound.


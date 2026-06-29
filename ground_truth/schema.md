# Ground Truth Schema

## CSV Columns

| Column | Required | Meaning |
| --- | --- | --- |
| `file_id` | yes | Stable ID used by benchmark outputs. Do not edit. |
| `file_path` | yes | Audio path. Do not edit unless files move. |
| `file_name` | yes | Audio filename for easier reading. |
| `language` | optional | Language code or language name, for example `vi`, `en`, `Vietnamese`. |
| `ground_truth_transcript` | yes | Human transcript. Preserve original language. |
| `ground_truth_tagged_transcript` | optional | Transcript with inline tags only when tag position is clear. |
| `nonverbal_tags_json` | optional | JSON array of human vocal/non-verbal tags. |
| `background_tags_json` | optional | JSON array of background/audio event tags. |
| `emotion_tags_json` | optional | JSON array of emotion labels. |
| `speech_present` | optional | `true` or `false`. |
| `multiple_speakers` | optional | `true` or `false`. |
| `noise_level` | optional | `low`, `medium`, `high`, or `unknown`. |
| `annotator` | optional | Annotator name or ID. |
| `review_status` | yes | `draft`, `reviewed`, or `needs_review`. |
| `notes` | optional | Free-form annotation notes. |

## Non-Verbal And Background Labels

Use only these canonical labels:

```text
laughter
crying
cough
sneeze
sigh
scream
applause
music
background_noise
traffic
rain
door_sound
phone_ring
alarm
silence
unknown_sound
```

Recommended tag object:

```json
{
  "label": "laughter",
  "evidence": "short laugh after the sentence",
  "time_status": "global"
}
```

Timestamped tag object:

```json
{
  "label": "music",
  "evidence": "background music",
  "time_status": "timestamped",
  "start": 1.2,
  "end": 5.8
}
```

## Emotion Labels

Use only these labels:

```text
neutral
happy
sad
angry
fearful
calm
excited
stressed
uncertain_emotion
not_applicable
```

Recommended emotion object:

```json
{
  "label": "neutral",
  "evidence": "speaker tone is steady",
  "scope": "whole_audio"
}
```

Rules:

- If no speech or human vocal sound exists, use `not_applicable`.
- If emotion is unclear, use `uncertain_emotion`.
- Do not infer emotion from transcript meaning alone; label from audible tone.
- Do not invent timestamps.


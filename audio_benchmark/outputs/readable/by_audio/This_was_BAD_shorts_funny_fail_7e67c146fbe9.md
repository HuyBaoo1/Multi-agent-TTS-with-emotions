# This was BAD  #shorts   #funny   #fail.mp3

- File ID: `This_was_BAD_shorts_funny_fail_7e67c146fbe9`
- Path: `audio\Audio-short\This was BAD  #shorts   #funny   #fail.mp3`

## Model Summary

| Model | Status | Transcript | Tags | Emotion | Error |
| --- | --- | ---: | ---: | --- | --- |
| elevenlabs_scribe_v2 | success | 110 | 2 |  |  |
| gemini_gemini-3.1-pro-preview | success | 90 | 0 | excited, uncertain_emotion, neutral |  |
| gemini_gemini-3.5-flash | success | 63 | 0 | excited |  |
| openai_gpt-4o-mini-transcribe | error | 0 | 0 |  | RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and ... |

## elevenlabs_scribe_v2

- Status: `success`
- Raw response: `audio_benchmark\outputs\raw\elevenlabs_scribe_v2_This_was_BAD_shorts_funny_fail_7e67c146fbe9.json`

### Transcript

```text
Throw the cards into the air on the count of three. One, two- [laughs] Yeah, s- sit down. Yes, ma'am. [laughs]
```

### Tagged Transcript

```text
Throw the cards into the air on the count of three. One, two- [laughs] Yeah, s- sit down. Yes, ma'am. [laughs]
```

### Segments

_No provider segments returned._

### Tags

**Non-verbal:**

| Label | Raw label | Confidence | Time | Evidence |
| --- | --- | --- | --- | --- |
| laughter | [laughs] |  | timestamped | [laughs] |
| laughter | [laughs] |  | timestamped | [laughs] |

**Background / noise:** none

**Emotion:** none

### Metadata

- Language: `eng`
- Word timestamps available: `True`
- Word count returned: `19`
- Quality: `{"confidence": "unknown", "multiple_speakers": true, "noise_level": "unknown", "speech_present": true}`
- Reliability: `{"emotion_confidence": "unknown", "nonverbal_confidence": "unknown", "overall_confidence": "unknown", "transcript_confidence": "unknown"}`

## gemini_gemini-3.1-pro-preview

- Status: `success`
- Raw response: `audio_benchmark\outputs\raw\gemini_gemini-3.1-pro-preview_This_was_BAD_shorts_funny_fail_7e67c146fbe9.json`

### Transcript

```text
Throw the cards into the air! On the count of three, one, two... Oh sorry. Yeah, sit down.
```

### Tagged Transcript

```text
Throw the cards into the air! On the count of three, one, two... [laughter] Oh sorry. Yeah, sit down. [laughter]
```

### Segments

1. ``-`3.5` Throw the cards into the air! On the count of three, one, two...
2. `9.5`-`10.5` Oh sorry.
3. `11.0`-`12.0` Yeah, sit down.

### Tags

**Non-verbal:** none

**Background / noise:** none

**Emotion:**

| Label | Confidence | Scope | Evidence |
| --- | --- | --- | --- |
| excited |  | whole_audio |  |
| uncertain_emotion |  | whole_audio |  |
| neutral |  | whole_audio |  |

### Metadata

- Language: `en`
- Word timestamps available: `True`
- Word count returned: `18`
- Quality: `{"confidence": "high", "multiple_speakers": true, "noise_level": "medium", "speech_present": true}`
- Reliability: `{"emotion_confidence": "high", "nonverbal_confidence": "high", "overall_confidence": "high", "transcript_confidence": "high"}`

## gemini_gemini-3.5-flash

- Status: `success`
- Raw response: `audio_benchmark\outputs\raw\gemini_gemini-3.5-flash_This_was_BAD_shorts_funny_fail_7e67c146fbe9.json`

### Transcript

```text
Throw the cars into the air! On the count of three, one, two...
```

### Tagged Transcript

```text
Throw the cars into the air! On the count of three, one, two... [laughter] [cheering]
```

### Segments

1. ``-`1.8` Throw the cars into the air!
2. `1.8`-`4.5` On the count of three, one, two...

### Tags

**Non-verbal:** none

**Background / noise:** none

**Emotion:**

| Label | Confidence | Scope | Evidence |
| --- | --- | --- | --- |
| excited |  | whole_audio |  |

### Metadata

- Language: `en`
- Word timestamps available: `True`
- Word count returned: `13`
- Quality: `{"confidence": "high", "multiple_speakers": true, "noise_level": "medium", "speech_present": true}`
- Reliability: `{"emotion_confidence": "high", "nonverbal_confidence": "high", "overall_confidence": "high", "transcript_confidence": "high"}`

## openai_gpt-4o-mini-transcribe

- Status: `error`
- Raw response: `audio_benchmark\outputs\raw\openai_gpt-4o-mini-transcribe_This_was_BAD_shorts_funny_fail_7e67c146fbe9.json`

Error:

```text
RateLimitError: Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details. For more information on this error, read the docs: https://platform.openai.com/docs/guides/error-codes/api-errors.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}}
```

### Transcript

```text

```

### Tagged Transcript

```text

```

### Segments

_No provider segments returned._

### Tags

**Non-verbal:** none

**Background / noise:** none

**Emotion:** none

### Metadata

- Language: ``
- Word timestamps available: `False`
- Word count returned: `0`
- Quality: `{"confidence": "unknown", "multiple_speakers": false, "noise_level": "unknown", "speech_present": false}`
- Reliability: `{"emotion_confidence": "unknown", "nonverbal_confidence": "unknown", "overall_confidence": "unknown", "transcript_confidence": "unknown"}`

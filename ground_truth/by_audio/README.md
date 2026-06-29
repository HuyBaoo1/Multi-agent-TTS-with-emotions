# Per-Audio Ground Truth CSVs

Each CSV in this folder contains one audio row from `ground_truth/audio_short_ground_truth_template.csv`.

Use these files when it is easier to annotate one audio at a time.

Recommended flow:

1. Open one CSV file.
2. Listen to the matching `file_path`.
3. Fill transcript, tagged transcript, tag JSON, emotion JSON, and quality fields.
4. Change `review_status` from `draft` to `reviewed` after checking it.

`index.csv` maps every audio file to its per-audio CSV.

Keep the `file_id` unchanged. It is the key used to compare model outputs against ground truth.


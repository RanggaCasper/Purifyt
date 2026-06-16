# Dataset Guide

Purifyt stores YouTube comments as datasets. Each dataset can contain comments imported from YouTube, Kaggle, manual flows, or explorer workflows.

## Comment Schema

| Column | Description |
|--------|-------------|
| `video_id` | YouTube video identifier. |
| `title` | Video title. |
| `channel_name` | YouTube channel name. |
| `date` | Comment or video publish date. |
| `author` | Comment author. |
| `comment` | Raw comment text. |
| `label` | Human-provided sentiment/category label when available. |
| `clean_comment` | Preprocessed comment text used by downstream workflows. |
| `predicted_label` | Model-predicted label. |
| `source` | Data origin such as `youtube_api`, `kaggle`, or manual import. |
| `source_detail` | Specific source information such as video URL, Kaggle slug, or filename. |

## Import Sources

| Source | Description |
|--------|-------------|
| YouTube API | Searches videos and imports comments directly from YouTube Data API flows. |
| Kaggle | Downloads or imports CSV datasets from Kaggle. |
| Explorer | Scans a video or channel and streams progress while saving/classifying comments. |
| Manual | Data inserted through user-driven workflows or API calls. |

## Cleaning Flow

The text cleaner normalizes noisy comment text before storage or classification. The pipeline handles common YouTube comment artifacts such as emojis, repeated punctuation, zero-width characters, and noisy URL/token patterns.

Cleaned comments are stored separately from raw comments so the original source text remains available.

## Prediction Flow

```text
Raw comment
  -> text cleaner
  -> BERT model inference
  -> predicted_label
  -> stored comment result
```

Predictions can be run for a single comment, a batch of comments, or an existing dataset.

## Dataset Management

Datasets can be listed, opened with comments, searched, and deleted through the authenticated API and web UI.

# Purifyt

Purifyt is a YouTube comment moderation and dataset platform for collecting comments, cleaning text, managing datasets, classifying online gambling comments, and assisting YouTube Studio cleanup workflows. It includes a FastAPI backend, a Nuxt web interface, and a Tauri desktop shell.

![Purifyt predict page](docs/assets/predict.png)

## Table of Contents

- [Overview](#overview)
- [Auto Delete Workflow](#auto-delete-workflow)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Project Structure](#project-structure)
- [Development](#development)

## Overview

Purifyt helps build and maintain YouTube comment datasets for online gambling comment detection. The application can import comments from YouTube, import datasets from Kaggle, normalize comment text, run BERT-based predictions, manually correct labels, and expose the result through API, web UI, and desktop app workflows.

The backend stores data in MySQL during local development using async SQLAlchemy. Compiled standalone builds switch to SQLite. Authentication uses short-lived JWT access tokens and rotated HttpOnly refresh-token cookies. Long-running explorer and auto-delete flows stream progress through server-sent events.

## Auto Delete Workflow
The auto-delete workflow connects Purifyt to YouTube Studio through a saved Google cookie session, scans video comments, predicts which comments are online gambling spam, lets the user preview the result, and deletes selected spam comments from YouTube Studio.

```mermaid
flowchart TD
    A[Login with Google account] --> B[Save YouTube Studio cookie session]
    B --> C[Open Auto Delete page]
    C --> D[Enter YouTube video URL or video ID]
    D --> E[Select saved Google account]
    E --> F[Set detection threshold]
    F --> G{Preview or Delete?}
    G -->|Preview| H[Fetch comments from YouTube Studio]
    G -->|Delete| H
    H --> I[Clean comment text]
    I --> J[Run BERT gambling-spam prediction]
    J --> K[Show detected spam comments]
    K --> L{Delete mode?}
    L -->|No| M[Review results safely]
    L -->|Yes| N[Delete detected comments in YouTube Studio]
    N --> O[Show deletion summary and logs]
```

Recommended usage:

1. Add or refresh a Google account cookie session from the Auto Delete page.
2. Run Preview first to inspect detected comments without deleting anything.
3. Adjust the threshold if there are too many false positives or missed spam comments.
4. Run Delete only after the preview result looks correct.
5. Review the final logs to confirm how many comments were scanned, detected, and deleted.


## Features

- YouTube Data API integration for searching videos and importing comments.
- YouTube scan flow for prediction without saving results.
- Kaggle CSV import for external dataset ingestion.
- Dataset management with comment listing, search, manual dataset creation, and deletion workflows.
- BERT-based binary classification for detecting judi online comments.
- Manual label correction for single comments and bulk dataset corrections.
- Text cleaning pipeline for emojis, repeated punctuation, zero-width characters, URLs, and noisy text.
- Video explorer and channel explorer with server-sent event progress updates.
- Auto-delete assistant for YouTube Studio cookie login, comment scanning, preview, deletion, and cookie-account management.
- JWT authentication with access tokens and rotated HttpOnly refresh-token cookies.
- Settings API for YouTube and Kaggle credentials stored in the database.
- Nuxt web application with internationalization support.
- Tauri desktop app support for packaging the frontend as a desktop application.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, SQLAlchemy Async, Pydantic, Server-Sent Events |
| Database | MySQL for development, SQLite for compiled standalone builds |
| ML | Transformers / BERT model assets |
| Frontend | Nuxt 4, Vue, Pinia, Nuxt UI, Tailwind CSS |
| Desktop | Tauri 2 |
| Testing | Pytest |

## Quick Start

### Backend

```bash
git clone https://github.com/RanggaCasper/Purifyt.git
cd Purifyt
pip install -r requirements.txt
cp .env.example .env
```

Create the database:

```sql
CREATE DATABASE purifyt CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Run the API:

```bash
uvicorn app.main:app --reload
```

Open `http://localhost:51441/docs` for the Swagger UI.

### Website

```bash
cd website
pnpm install
pnpm dev
```

### Desktop App

```bash
cd website
pnpm desktop
```

Build the desktop app:

```bash
cd website
pnpm build:desktop
```

## Documentation

Longer documentation is split into `docs/`:

| Document | Description |
|----------|-------------|
| [Setup Guide](docs/setup.md) | Environment variables, backend, frontend, desktop, and test setup. |
| [API Reference](docs/api.md) | Main API endpoint groups and request/response examples. |
| [Architecture](docs/architecture.md) | Backend, frontend, desktop, database, and service structure. |
| [Dataset Guide](docs/dataset.md) | Dataset schema, source tracking, and comment processing flow. |

## Project Structure

```text
Purifyt/
├── app/                  # FastAPI backend
│   ├── api/              # API router and versioned endpoints
│   ├── core/             # Runtime config and logging
│   ├── db/               # Async DB connection and ORM models
│   ├── modules/          # Feature modules and services
│   └── shared/           # Shared utilities and data
├── docs/                 # Project documentation and screenshots
├── model/                # BERT model assets
├── tests/                # Backend tests
├── website/              # Nuxt frontend and Tauri desktop shell
├── .env.example          # Environment variable template
├── purifyt.spec          # PyInstaller spec
├── requirements.txt      # Python dependencies
└── README.md
```

See [Architecture](docs/architecture.md) for the detailed module breakdown.

## Development

Useful commands:

| Command | Description |
|---------|-------------|
| `uvicorn app.main:app --reload --port 51441` | Run the backend API locally on the frontend default API port. |
| `pytest` | Run backend tests. |
| `cd website && pnpm dev` | Run the Nuxt web app. |
| `cd website && pnpm build` | Build the Nuxt web app. |
| `cd website && pnpm lint` | Run frontend linting. |
| `cd website && pnpm typecheck` | Run Nuxt/Vue type checking. |
| `cd website && pnpm desktop` | Run the Tauri desktop app in development. |
| `cd website && pnpm build:desktop` | Build the desktop app. |

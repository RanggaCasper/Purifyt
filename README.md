# Purifyt

Purifyt is a YouTube comment dataset platform for collecting comments, cleaning text, managing datasets, and classifying comments with a BERT-based model. It includes a FastAPI backend, a Nuxt web interface, and a Tauri desktop shell.

![Purifyt landing page](docs/assets/landing.png)

## Table of Contents

- [Overview](#overview)
- [Screenshots](#screenshots)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Documentation](#documentation)
- [Project Structure](#project-structure)
- [Development](#development)

## Overview

Purifyt helps build and maintain YouTube comment datasets for online gambling comment detection. The application can import comments from YouTube, import CSV datasets from Kaggle, normalize comment text, run model predictions, and expose the result through API, web UI, and desktop app workflows.

The backend stores data in MySQL using async SQLAlchemy. Authentication uses JWT access and refresh tokens with token blacklisting. Long-running explorer flows stream progress through server-sent events.

## Prediction Workflow
The prediction workflow takes raw comments, cleans the text, runs inference through a BERT model, and stores the predicted label alongside the original comment.


![Purifyt prediction page](docs/assets/predict.png)

## Features

- YouTube Data API integration for searching videos and importing comments.
- Kaggle CSV import for external dataset ingestion.
- Dataset management with comment listing, search, update, and deletion workflows.
- BERT-based binary classification for detecting judi online comments.
- Text cleaning pipeline for emojis, repeated punctuation, zero-width characters, URLs, and noisy text.
- Video explorer and channel explorer with server-sent event progress updates.
- JWT authentication with access token, refresh token, logout, and token blacklist support.
- Settings API for application configuration stored in the database.
- Nuxt web application with internationalization support.
- Tauri desktop app support for packaging the frontend as a desktop application.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI, SQLAlchemy Async, Pydantic |
| Database | MySQL |
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
| [Use Case Specification](docs/use_case_specification.md) | Functional use-case details. |
| [Postman Collection](docs/postman_collection.json) | API collection for manual testing. |

## Project Structure

```text
Purifyt/
├── app/                  # FastAPI backend
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
| `uvicorn app.main:app --reload` | Run the backend API locally. |
| `pytest` | Run backend tests. |
| `cd website && pnpm dev` | Run the Nuxt web app. |
| `cd website && pnpm lint` | Run frontend linting. |
| `cd website && pnpm typecheck` | Run Nuxt/Vue type checking. |
| `cd website && pnpm desktop` | Run the Tauri desktop app in development. |
| `cd website && pnpm build:desktop` | Build the desktop app. |

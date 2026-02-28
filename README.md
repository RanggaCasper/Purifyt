# Purifyt – YouTube Comment Dataset API

A **FastAPI** backend for collecting, storing, and managing YouTube comment datasets. Supports importing data from **YouTube Data API v3** and **Kaggle**, stored in **MySQL**.

## Features

- **YouTube API v3 Integration** – Search videos and import comments directly
- **Kaggle Import** – Download and import CSV datasets from Kaggle
- **MySQL Storage** – All data persisted in MySQL with async SQLAlchemy
- **JWT Authentication** – Access + refresh token pair with token blacklisting
- **Token Blacklist** – Revoke tokens on logout; blacklisted tokens are rejected
- **Video Explorer** – Scan a video's comments, classify judi/normal via BERT model (SSE)
- **Channel Explorer** – Scan an entire channel's recent videos (SSE)
- **Auto-Labeling** – BERT-based binary classification (judi online vs normal)
- **Text Cleaner** – Emoji removal, repeated punctuation collapse, zero-width char strip
- **Source Tracking** – Every comment records its origin (YouTube API, Kaggle, or manual)
- **RESTful API** – Full CRUD with Swagger docs at `/docs`

## Dataset Schema

Each comment record contains:

| Column            | Description                        |
|-------------------|------------------------------------|
| `video_id`        | YouTube video identifier           |
| `title`           | Video title                        |
| `channel_name`    | YouTube channel name               |
| `date`            | Comment/video publish date         |
| `author`          | Comment author                     |
| `comment`         | Raw comment text                   |
| `label`           | Sentiment/category label           |
| `clean_comment`   | Preprocessed comment text          |
| `predicted_label` | Model-predicted label              |
| `source`          | Data origin (youtube_api / kaggle) |
| `source_detail`   | Specific source info (URL / slug)  |

## Project Structure

```
project/
├── app/
│   ├── main.py                  # FastAPI application entry point
│   ├── api/
│   │   ├── router.py            # Root API router
│   │   └── v1/
│   │       ├── auth.py          # Register / Login / Refresh / Logout / Me
│   │       ├── users.py         # User management
│   │       ├── datasets.py      # Dataset CRUD + comment listing
│   │       ├── youtube.py       # YouTube search & import
│   │       ├── kaggle.py        # Kaggle dataset import
│   │       ├── labeling.py      # Predict & auto-label endpoints
│   │       ├── explorer.py      # Video explorer (SSE)
│   │       └── channel_explorer.py  # Channel explorer (SSE)
│   ├── core/
│   │   ├── schemas.py           # Pydantic request/response models
│   │   └── services/
│   │       ├── auth_service.py  # Password hashing, JWT (access+refresh), blacklist
│   │       ├── model_service.py # BERT model inference
│   │       ├── explorer_service.py
│   │       ├── channel_explorer_service.py
│   │       ├── youtube_service.py
│   │       └── kaggle_service.py
│   ├── db/
│   │   ├── connection.py        # Async SQLAlchemy engine & session
│   │   ├── models.py            # ORM models (User, Dataset, Comment, TokenBlacklist)
│   │   └── repositories/
│   │       ├── user_repository.py
│   │       ├── dataset_repository.py
│   │       └── comment_repository.py
│   ├── config/
│   │   └── settings.py          # Pydantic settings from .env
│   └── utils/
│       └── text_cleaner.py      # Comment text cleaning pipeline
├── model/                       # BERT model files (safetensors)
├── tests/
│   └── test_api.py
├── Dockerfile
├── requirements.txt
├── postman_collection.json
└── README.md
```

## Quick Start

### 1. Clone & Install

```bash
git clone <repo-url>
cd Purifyt
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your MySQL credentials, YouTube API key, and Kaggle creds
```

### 3. Create MySQL Database

```sql
CREATE DATABASE purifyt CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. Run

```bash
uvicorn app.main:app --reload
```

Open **http://localhost:8000/docs** for interactive Swagger UI.

## API Endpoints

### Auth
| Method | Endpoint                  | Auth | Description                              |
|--------|---------------------------|------|------------------------------------------|
| POST   | `/api/v1/auth/register`   | No   | Create a new user                        |
| POST   | `/api/v1/auth/login`      | No   | Get access_token + refresh_token         |
| POST   | `/api/v1/auth/refresh`    | No   | Exchange refresh_token for new pair      |
| POST   | `/api/v1/auth/logout`     | Yes  | Revoke current access_token              |
| POST   | `/api/v1/auth/logout/all` | Yes  | Revoke access_token + refresh_token      |
| GET    | `/api/v1/auth/me`         | Yes  | Current user info                        |

**Login response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Refresh request:**
```json
{ "refresh_token": "eyJ..." }
```

**Logout /all request (optional body):**
```json
{ "refresh_token": "eyJ..." }
```

### Users
| Method | Endpoint              | Description      |
|--------|-----------------------|------------------|
| GET    | `/api/v1/users/`      | List all users   |
| GET    | `/api/v1/users/{id}`  | Get user by ID   |

### Datasets
| Method | Endpoint                             | Description            |
|--------|--------------------------------------|------------------------|
| GET    | `/api/v1/datasets/`                  | List datasets          |
| GET    | `/api/v1/datasets/{id}`              | Get dataset + comments |
| DELETE | `/api/v1/datasets/{id}`              | Delete dataset         |
| GET    | `/api/v1/datasets/{id}/comments`     | List comments          |
| GET    | `/api/v1/datasets/search/comments`   | Search comments        |

### YouTube
| Method | Endpoint                  | Description                         |
|--------|---------------------------|-------------------------------------|
| GET    | `/api/v1/youtube/search`  | Search YouTube videos               |
| POST   | `/api/v1/youtube/import`  | Fetch & save comments from a video  |

### Kaggle
| Method | Endpoint                 | Description                      |
|--------|--------------------------|----------------------------------|
| POST   | `/api/v1/kaggle/import`  | Import a Kaggle CSV dataset      |

### Labeling
| Method | Endpoint                          | Auth | Description                      |
|--------|-----------------------------------|------|----------------------------------|
| POST   | `/api/v1/labeling/predict`        | No   | Classify a single comment        |
| POST   | `/api/v1/labeling/predict/batch`  | No   | Classify a batch of comments     |
| POST   | `/api/v1/labeling/dataset/{id}`   | Yes  | Auto-label all comments in a dataset |

### Explorer
| Method | Endpoint                          | Auth | Description                      |
|--------|-----------------------------------|------|----------------------------------|
| POST   | `/api/v1/explorer/run`            | Yes  | Explore a video's comments (SSE) |
| POST   | `/api/v1/explorer/channel/run`    | Yes  | Explore a channel (SSE)          |

## Token Lifecycle

```
Login ─► access_token (30 min) + refresh_token (7 days)
           │
           ├── Use access_token for API calls
           │
           ├── When expired ─► POST /auth/refresh with refresh_token
           │                   ─► new access_token + new refresh_token
           │                      (old refresh_token is blacklisted)
           │
           ├── POST /auth/logout ─► blacklist access_token
           │
           └── POST /auth/logout/all ─► blacklist both tokens
```

Blacklisted tokens are stored in the `token_blacklist` table and rejected on subsequent requests. Expired blacklist entries are automatically cleaned up.

## Docker

```bash
docker build -t purifyt .
docker run -p 8000:8000 --env-file .env purifyt
```

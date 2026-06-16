# Architecture

Purifyt is split into three main runtime surfaces: FastAPI backend, Nuxt website, and Tauri desktop app.

## Backend

The backend lives in `app/`.

```text
app/
├── main.py                  # FastAPI application entry point
├── standalone.py            # Standalone runtime entry point
├── api/
│   ├── router.py            # Root API router with /api/v1 prefix
│   └── v1/                  # Versioned endpoint modules
├── config/                  # Settings and logging configuration
├── core/
│   ├── schemas.py           # Pydantic models
│   └── services/            # Business logic and integrations
├── db/
│   ├── connection.py        # Async SQLAlchemy engine/session
│   ├── models.py            # ORM models
│   └── repositories/        # Database access layer
└── utils/                   # Shared utility functions
```

## API Layer

`app/api/router.py` mounts every versioned API module under `/api/v1`. Most route groups use the current-user dependency, while auth endpoints expose registration, login, refresh, logout, and profile retrieval.

Endpoint modules are intentionally thin. They validate requests, call services or repositories, and return Pydantic responses.

## Services

The service layer coordinates integrations and longer workflows.

| Service | Responsibility |
|---------|----------------|
| `auth_service.py` | Password hashing, JWT creation, token validation, and blacklist checks. |
| `model_service.py` | Model loading and comment classification. |
| `youtube_service.py` | YouTube search and comment import. |
| `kaggle_service.py` | Kaggle dataset import. |
| `explorer_service.py` | Video exploration workflow. |
| `channel_explorer_service.py` | Channel-level exploration workflow. |
| `auto_delete_service.py` | Automated deletion workflow. |
| `cookie_manager.py` | Cookie/profile handling for browser automation flows. |

## Database

The database layer uses async SQLAlchemy. ORM models are defined in `app/db/models.py`, while repositories isolate database reads and writes.

Main entities include users, datasets, comments, token blacklist entries, and application settings.

## Frontend

The frontend lives in `website/` and uses Nuxt 4.

```text
website/
├── app/
│   ├── composables/         # API and app composables
│   ├── pages/               # Nuxt pages
│   ├── stores/              # Pinia stores
│   └── types/               # TypeScript types
├── i18n/                    # Locale files
├── public/                  # Static assets
├── src-tauri/               # Tauri desktop shell
├── package.json
└── nuxt.config.ts
```

The frontend talks to the FastAPI backend through API composables and maintains user/session state with Pinia.

## Desktop App

The Tauri app in `website/src-tauri` packages the Nuxt UI as a desktop application. Development uses `pnpm desktop`, while production builds use `pnpm build:desktop`.

## Data Flow

```text
Nuxt/Tauri UI
  -> FastAPI /api/v1 routes
  -> Service layer
  -> Repository layer
  -> MySQL
```

For prediction and explorer flows, the service layer also calls model inference and YouTube/Kaggle integrations before persisting or returning results.

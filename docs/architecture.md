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
├── core/                    # Settings and logging configuration
├── db/
│   ├── connection.py        # Async SQLAlchemy engine/session
│   └── models/              # ORM models grouped by entity
├── modules/                 # Feature modules with schemas, services, repositories
└── shared/                  # Shared utilities and static data
```

## API Layer

`app/api/router.py` mounts every versioned API module under `/api/v1`. Most route groups use the current-user dependency at router registration, while auth endpoints expose registration, login, refresh, logout, and profile retrieval.

Endpoint modules are intentionally thin. They validate requests, call services or repositories, and return Pydantic responses.

## Services

Feature modules in `app/modules/` coordinate integrations, repositories, schemas, and longer workflows.

| Module | Responsibility |
|--------|----------------|
| `auth` | User repository, password hashing, JWT access tokens, refresh-token rotation, and auth dependencies. |
| `datasets` | Dataset and comment repositories plus dataset/comment schemas. |
| `labeling` | BERT model loading, text cleaning, single/batch prediction, dataset labeling, and manual label correction. |
| `youtube` | YouTube video search, comment fetch/import, and scan-without-save flows. |
| `kaggle` | Kaggle dataset import with optional column mapping. |
| `explorer` | Video and channel exploration workflows with SSE progress. |
| `automation` | YouTube Studio browser automation, cookie management, scan preview, and comment deletion. |
| `settings` | Database-backed YouTube/Kaggle credential settings. |

## Database

The database layer uses async SQLAlchemy. ORM models are defined in `app/db/models/`, while repositories in feature modules isolate database reads and writes.

Main entities include users, datasets, comments, refresh tokens, legacy token blacklist entries, cookie accounts, and application settings.

Source runs use MySQL. Compiled standalone runs use SQLite via `Settings.DATABASE_URL`.

## Frontend

The frontend lives in `website/` and uses Nuxt 4.

```text
website/
├── app/
│   ├── components/          # Shared and feature UI components
│   ├── composables/         # API and app composables
│   ├── layouts/             # Landing, auth, and authenticated layouts
│   ├── middleware/          # Auth and guest route guards
│   ├── pages/               # Nuxt pages
│   ├── stores/              # Pinia stores
│   └── types/               # TypeScript types
├── i18n/                    # Locale files
├── public/                  # Static assets
├── src-tauri/               # Tauri desktop shell
├── package.json
└── nuxt.config.ts
```

The frontend talks to the FastAPI backend through API composables, uses `NUXT_PUBLIC_API_BASE`/runtime config for the API URL, and maintains user/session state with Pinia.

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

Authentication flow:

```text
Login
  -> access_token in JSON response
  -> refresh_token stored as HttpOnly cookie
  -> refresh rotates the refresh token row and cookie
  -> logout revokes the active refresh token and clears the cookie
```

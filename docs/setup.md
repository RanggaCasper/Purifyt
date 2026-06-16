# Setup Guide

This guide covers local setup for the FastAPI backend, Nuxt website, and Tauri desktop application.

## Requirements

| Tool | Purpose |
|------|---------|
| Python 3.11+ | Backend runtime and tests. |
| MySQL | Application database. |
| Node.js | Frontend runtime. |
| pnpm 10.29.3+ | Frontend package manager. |
| Rust | Required by Tauri desktop builds. |

## Backend Setup

Install Python dependencies from the repository root:

```bash
pip install -r requirements.txt
```

Create an environment file:

```bash
cp .env.example .env
```

Configure `.env` with database, JWT, cookie, and CORS settings.

| Variable | Description |
|----------|-------------|
| `APP_NAME` | Application name used by the backend. |
| `APP_VERSION` | Application version string. |
| `DEBUG` | Enables development behavior when `true`. |
| `MYSQL_HOST` | MySQL host. |
| `MYSQL_PORT` | MySQL port. |
| `MYSQL_USER` | MySQL user. |
| `MYSQL_PASSWORD` | MySQL password. |
| `MYSQL_DATABASE` | MySQL database name. |
| `SECRET_KEY` | JWT signing key. Use a strong random value in production. |
| `ALGORITHM` | JWT algorithm, usually `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime. |
| `COOKIE_SECURE` | Set to `true` when serving over HTTPS. |
| `COOKIE_SAMESITE` | Cookie SameSite policy. |
| `COOKIE_DOMAIN` | Optional cookie domain. |
| `CORS_ORIGINS` | JSON array of allowed frontend origins. |

Create the database:

```sql
CREATE DATABASE purifyt CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Run the backend:

```bash
uvicorn app.main:app --reload
```

The API documentation is available at `http://localhost:8000/docs`.

## Website Setup

Install frontend dependencies:

```bash
cd website
pnpm install
```

Run the web app:

```bash
pnpm dev
```

The Nuxt app runs separately from the FastAPI backend. Make sure CORS allows the Nuxt origin configured in `.env`.

## Desktop Setup

The desktop app uses Tauri in `website/src-tauri` and reuses the Nuxt frontend.

Run the desktop app in development:

```bash
cd website
pnpm desktop
```

Build the desktop app:

```bash
cd website
pnpm build:desktop
```

## Tests

Run backend tests from the repository root:

```bash
pytest
```

Run frontend checks from `website/`:

```bash
pnpm lint
pnpm typecheck
```

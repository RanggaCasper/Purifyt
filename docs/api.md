# API Reference

The API is served under `/api/v1`. Interactive documentation is available at `/docs` when the FastAPI server is running.

## Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/auth/register` | No | Create a new user. |
| `POST` | `/api/v1/auth/login` | No | Get an access token and refresh token. |
| `POST` | `/api/v1/auth/refresh` | No | Exchange a refresh token for a new token pair. |
| `POST` | `/api/v1/auth/logout` | Yes | Revoke the current access token. |
| `POST` | `/api/v1/auth/logout/all` | Yes | Revoke both access and refresh tokens. |
| `GET` | `/api/v1/auth/me` | Yes | Get the current user profile. |

Login response:

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

Refresh request:

```json
{
  "refresh_token": "eyJ..."
}
```

Logout all request:

```json
{
  "refresh_token": "eyJ..."
}
```

## Users

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/users/` | Yes | List all users. |
| `GET` | `/api/v1/users/{id}` | Yes | Get a user by ID. |

## Datasets

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/datasets/` | Yes | List datasets. |
| `GET` | `/api/v1/datasets/{id}` | Yes | Get a dataset with comments. |
| `DELETE` | `/api/v1/datasets/{id}` | Yes | Delete a dataset. |
| `GET` | `/api/v1/datasets/{id}/comments` | Yes | List comments in a dataset. |
| `GET` | `/api/v1/datasets/search/comments` | Yes | Search comments. |

## YouTube

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/youtube/search` | Yes | Search YouTube videos. |
| `POST` | `/api/v1/youtube/import` | Yes | Fetch and save comments from a video. |

## Kaggle

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/kaggle/import` | Yes | Import a Kaggle CSV dataset. |

## Labeling

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/labeling/predict` | Yes | Classify one comment. |
| `POST` | `/api/v1/labeling/predict/batch` | Yes | Classify multiple comments. |
| `POST` | `/api/v1/labeling/dataset/{id}` | Yes | Auto-label all comments in a dataset. |

## Explorer

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/explorer/run` | Yes | Explore one video's comments with SSE progress. |
| `POST` | `/api/v1/explorer/channel/run` | Yes | Explore a channel with SSE progress. |

## Auto Delete

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/auto-delete/run` | Yes | Run automated deletion flow when configured. |

## Settings

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/settings` | Yes | Get application settings. |
| `PUT` | `/api/v1/settings` | Yes | Update application settings. |

## Token Lifecycle

```text
Login -> access_token + refresh_token
  -> use access_token for authenticated API calls
  -> refresh with refresh_token when access_token expires
  -> old refresh_token is blacklisted after refresh
  -> logout blacklists the active access_token
  -> logout/all blacklists both tokens
```

Blacklisted tokens are stored in the `token_blacklist` table and rejected on later requests. Expired blacklist entries are cleaned up automatically.

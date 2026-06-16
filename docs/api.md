# API Reference

The API is served under `/api/v1`. Interactive documentation is available at `/docs` when the FastAPI server is running.

## Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/auth/register` | No | Create a new user. |
| `POST` | `/api/v1/auth/login` | No | Get an access token and set the refresh-token cookie. |
| `POST` | `/api/v1/auth/refresh` | No | Rotate the refresh-token cookie and get a new access token. |
| `POST` | `/api/v1/auth/logout` | No | Revoke the refresh-token cookie and clear it. |
| `GET` | `/api/v1/auth/me` | Yes | Get the current user profile. |

Login response:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 900
}
```

Refresh and logout read the `refresh_token` HttpOnly cookie set by login.

## Users

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/users/` | Yes | List all users. |
| `GET` | `/api/v1/users/{id}` | Yes | Get a user by ID. |

## Datasets

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/datasets/` | Yes | List datasets. |
| `POST` | `/api/v1/datasets/` | Yes | Create a manual dataset. |
| `GET` | `/api/v1/datasets/{id}` | Yes | Get a dataset with comments. |
| `DELETE` | `/api/v1/datasets/{id}` | Yes | Delete a dataset. |
| `GET` | `/api/v1/datasets/{id}/comments` | Yes | List comments in a dataset. |
| `GET` | `/api/v1/datasets/search/comments` | Yes | Search comments. |

## YouTube

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/youtube/search` | Yes | Search YouTube videos. |
| `POST` | `/api/v1/youtube/import` | Yes | Fetch and save comments from a video. |
| `POST` | `/api/v1/youtube/scan` | Yes | Fetch comments and classify them without saving. |

## Kaggle

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/kaggle/import/{owner}/{dataset}` | Yes | Import a Kaggle dataset by URL path slug. |
| `POST` | `/api/v1/kaggle/import` | Yes | Import a Kaggle CSV dataset. |

## Labeling

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/labeling/predict` | Yes | Classify one comment. |
| `POST` | `/api/v1/labeling/predict/batch` | Yes | Classify multiple comments. |
| `POST` | `/api/v1/labeling/dataset/{id}` | Yes | Auto-label all comments in a dataset. |
| `PATCH` | `/api/v1/labeling/comment/{id}` | Yes | Set a manual label for one comment. |
| `DELETE` | `/api/v1/labeling/comment/{id}/label` | Yes | Reset a manual label. |
| `PATCH` | `/api/v1/labeling/dataset/{id}/bulk` | Yes | Set manual labels for many comments in one dataset. |

## Explorer

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/explorer/run` | Yes | Explore one video's comments with SSE progress. |
| `POST` | `/api/v1/explorer/channel/run` | Yes | Explore a channel with SSE progress. |

## Auto Delete

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/v1/auto-delete/login` | Yes | Log in to Google/YouTube Studio and save cookies through SSE. |
| `POST` | `/api/v1/auto-delete/scan` | Yes | Scan a video and delete detected comments through SSE. |
| `POST` | `/api/v1/auto-delete/scan/preview` | Yes | Scan a video without deleting comments. |
| `POST` | `/api/v1/auto-delete/delete` | Yes | Delete specific comment IDs through SSE. |
| `POST` | `/api/v1/auto-delete/comments` | Yes | Fetch raw YouTube Studio comments through SSE. |
| `GET` | `/api/v1/auto-delete/cookies` | Yes | List saved cookie accounts. |
| `GET` | `/api/v1/auto-delete/cookies/{email}` | Yes | Get a saved cookie account. |
| `DELETE` | `/api/v1/auto-delete/cookies/{email}` | Yes | Delete a saved cookie account and cookie file. |

## Settings

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/v1/settings/credentials` | Yes | Get YouTube/Kaggle credential status and stored values. |
| `PUT` | `/api/v1/settings/credentials` | Yes | Update YouTube/Kaggle credentials. |

## Token Lifecycle

```text
Login -> access_token JSON + refresh_token HttpOnly cookie
  -> use access_token for authenticated API calls
  -> refresh reads the cookie when access_token expires
  -> old refresh_token row is revoked after rotation
  -> logout revokes the active refresh token and clears the cookie
```

Refresh tokens are stored as hashes in `refresh_tokens`. `token_blacklist` still exists as a legacy table, but current auth uses refresh-token rotation and revocation.

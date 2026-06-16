# Purifyt Website

Nuxt 4 frontend for Purifyt. It provides the landing page, authentication screens, dashboard, dataset management, prediction tools, explorer workflows, settings, and auto-delete assistant UI.

The app uses Nuxt UI, Pinia, Tailwind CSS, and i18n. It can run as a web app or inside the Tauri desktop shell in `src-tauri/`.

## Setup

Make sure to install the dependencies:

```bash
pnpm install
```

The default API base is `http://127.0.0.1:51441`. Override it with `NUXT_PUBLIC_API_BASE` when needed:

```bash
NUXT_PUBLIC_API_BASE=http://127.0.0.1:8000 pnpm dev
```

## Development Server

Start the development server on `http://localhost:3000`:

```bash
pnpm dev
```

Run the FastAPI backend separately from the repository root:

```bash
uvicorn app.main:app --reload --port 51441
```

## Production

Build the application for production:

```bash
pnpm build
```

Locally preview production build:

```bash
pnpm preview
```

## Checks

```bash
pnpm lint
pnpm typecheck
```

## Desktop

Run the Tauri desktop app in development:

```bash
pnpm desktop
```

Build the desktop app:

```bash
pnpm build:desktop
```

## Structure

```text
website/
├── app/
│   ├── components/      # Shared and feature components
│   ├── composables/     # API/auth helpers
│   ├── layouts/         # Landing, auth, and app layouts
│   ├── middleware/      # Route guards
│   ├── pages/           # Nuxt routes
│   ├── stores/          # Pinia stores
│   └── types/           # TypeScript types
├── i18n/locales/        # Indonesian and English messages
├── public/              # Static assets
└── src-tauri/           # Tauri desktop shell
```

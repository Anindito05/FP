# Kindred frontend

React + Vite + TypeScript client for the wellness support API.

## Source layout

- `src/main.tsx` mounts the app and global stylesheet.
- `src/App.tsx` composes the app shell and page components.
- `src/components/` contains the header and welcome, auth, chat, settings, and reviewer screens.
- `src/hooks/useAppController.ts` owns page state and user workflows.
- `src/api/client.ts` handles HTTP requests, access tokens, and refresh rotation.
- `src/types.ts` holds shared API and view types.
- `src/style.css` contains the shared responsive visual system.

Configure `VITE_API_BASE_URL` in `.env`, then run `npm run dev`. Use `npm run build` and `npm run lint` for verification after installing dependencies.

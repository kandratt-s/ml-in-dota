# Front

Vite + React + TypeScript + Tailwind. Talks to the BFF over REST (`/api/start`,
`/api/stop`) and WebSocket (`/ws/predictions`).

## Dev

```bash
npm install
npm run dev
```

Environment overrides:

- `VITE_BFF_BASE_URL` (default `http://localhost:8080`)
- `VITE_BFF_WS_URL` (default: derived from base URL)

## Tests

```bash
npm test
```

## Production build

```bash
npm run build && npm run preview
```

The Docker image builds the static assets and serves them through nginx, which
also proxies `/api/*` and `/ws/*` to the BFF service.

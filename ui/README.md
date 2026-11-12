# Kiebitz UI

Static React + Vite app (TypeScript), deployed to Azure Static Web Apps. The browser calls the
two backend services directly; their URLs are baked in at build time.

```bash
cd ui
npm ci
npm run dev            # http://localhost:5173, expects games on :8001 and insights on :8002
npm test               # vitest + Testing Library
npm run test:coverage
npm run lint           # oxlint
npm run format:check   # prettier
npm run build          # static files in dist/
```

| Build-time variable     | Default                 |
| ----------------------- | ----------------------- |
| `VITE_GAMES_API_URL`    | `http://localhost:8001` |
| `VITE_INSIGHTS_API_URL` | `http://localhost:8002` |

`public/staticwebapp.config.json` sets security headers for Azure Static Web Apps.

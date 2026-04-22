# attention-detector-v0.1 — Audit Console

Live-model web app for the "Can AI Cheat?" demo lesson at Hackley, 2026-04-23.

Static site. `npm start` → `npx serve public -l $PORT`. Deployed on Railway.

See [CLAUDE.md](./CLAUDE.md) for full context, config, and deploy steps.

## Local dev

```bash
npx serve public -l 3000
```

Open http://localhost:3000. Demo mode runs automatically if `MODEL_URL` is empty.

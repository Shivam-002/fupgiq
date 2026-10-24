# Wind Forecast Monitor

Shows the latest GB wind forecast available when a day-ahead purchase is made, and how accurate past forecasts have been. Data from Elexon BMRS (WINDFOR forecasts, FUELHH actuals).

**Live app:** https://fupgiq.vercel.app

## Run locally

```bash
# backend → http://localhost:8000/api/docs
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000

# frontend → http://localhost:5173
cd frontend
npm install
npm run dev
```

Docker (both): `docker compose up --build` → http://localhost:8080

## Structure

```
backend/                  FastAPI (Python 3.12, uv)
  app/routers/            API endpoints: /api/forecast, /api/health
  app/services/forecast/  Forecast selection and accuracy maths
  app/services/energy/    Wind data interface + Elexon adapter + cache
  app/core/               Config, errors, time helpers
  tests/                  pytest suite
frontend/                 React + TypeScript (Vite)
  src/components/         App components and shadcn/ui primitives
  src/lib/                API client, types, formatting
  src/hooks/, providers/  Data fetching, theme, animations
```

## AI usage

Built with **Claude Code** for assisted development.

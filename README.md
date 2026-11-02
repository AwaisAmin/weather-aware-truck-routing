# Weather-Aware Truck Routing

A React + Django web app that helps a truck driver pick the safest route between two places,
based on forecast weather along each route, the truck's load weight, and travel time.

> Work in progress. Features, design notes and assumptions will be documented here as they land.

## Stack

| Layer | Tech |
|---|---|
| Frontend | React (Vite), Material UI, MapLibre GL |
| Backend | Django, Django REST Framework |
| Routing & geocoding | TomTom APIs (truck profile) |
| Weather | Open-Meteo hourly forecast |

## Project layout

```
backend/    Django API (config/ = project settings, routing/ = app logic)
frontend/   React single-page app
```

## Running locally

Requirements: Python 3.12+, Node 20+, and a free [TomTom API key](https://developer.tomtom.com).

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env               # then set TOMTOM_API_KEY
python manage.py runserver
```

Tests:

```bash
cd backend
pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev                         # http://localhost:5173, proxies /api to :8000
```

## Deployment

The API and the frontend deploy separately: the Django API as a Render web service, the React
app as a static site on Vercel.

### API on Render

1. In Render, choose **New → Blueprint** and select this repository. `render.yaml` defines the
   service (root `backend/`, gunicorn, health check `/api/health/`, generated secret key).
2. When prompted, set `TOMTOM_API_KEY` and `CORS_ALLOWED_ORIGINS` (the Vercel URL from the next
   step, for example `https://weather-truck-routing.vercel.app`, with no trailing slash).
3. Check `https://<service>.onrender.com/api/health/` returns `{"status": "ok"}`.

On Render's free plan the service sleeps after 15 minutes of inactivity, so the first request
after a pause can take about a minute.

### Frontend on Vercel

1. Import the repository in Vercel and set **Root Directory** to `frontend` (the Vite preset is
   detected automatically).
2. Add the environment variable `VITE_API_BASE_URL=https://<service>.onrender.com` and deploy.
3. If the Vercel URL changed, update `CORS_ALLOWED_ORIGINS` on Render to match.

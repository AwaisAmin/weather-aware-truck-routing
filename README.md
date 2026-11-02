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
pip install -r requirements.txt
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

# Weather-Aware Truck Routing

A React + Django web app that helps a truck driver pick the safest route between two places,
based on the forecast weather the truck will actually drive through, its load weight, and
travel time.

**Live demo:** https://frontend-plum-five-36.vercel.app
(API: https://backend-three-omega-88.vercel.app/api/health/)

## Features

- **Trip form**: origin and destination with address search, departure date/time (up to 5 days
  ahead), load weight in lb, and checkpoint spacing of 10, 25 or 50 miles.
- **Three route options** from TomTom's truck routing, which accounts for the truck's gross
  weight.
- **Weather at the truck's ETA**: each checkpoint uses the hourly forecast for the time the truck
  is expected to reach it, not the weather at departure.
- **Risk scoring** using the assessment's risk table plus the load rules. Every checkpoint shows
  its level and which factor drove it (wind, rain, snow or wind + load).
- **Recommendation** with a one-line reason, for example "fewer High miles than the next best
  route".
- **Interactive map** (MapLibre):
  - routes drawn in their own colors, with checkpoints colored by risk;
  - click a route or its card to select it;
  - click a checkpoint for its ETA, conditions and risk;
  - checkpoint list synced with the map.
- **Corridor weather heatmap** with a 0–48 h slider and playback. A truck marker moves along the
  selected route in step with the slider, so you can see what weather it will meet and when.
- **Responsive layout**: a sidebar on desktop; on mobile the form, map and results stack.

## How it works

```
Browser ──► /api/plan/ ──► TomTom geocode + truck routes (3 alternatives)
                         ├► sample checkpoints every N miles, ETA from TomTom's time profile
                         ├► Open-Meteo hourly forecast per checkpoint (batched, cached)
                         ├► risk per checkpoint → route scores → ranking
                         └► JSON: routes, checkpoints, scores, recommendation
        ──► /api/heatmap/ ─► grid cells along the corridor × 49 hours of risk scores
```

### Risk rules

The checkpoint level is the worst of wind, rain and snow, then raised by the load rules:

| Level | Wind (mph) | Rain (in/hr) | Snow (in/hr) |
|---|---|---|---|
| Low | < 25 | < 0.10 | < 0.5 |
| Moderate | 25–35 | 0.10–0.25 | 0.5–1.0 |
| High | 35–45 | 0.25–0.50 | 1.0–2.0 |
| Severe | 45–55 | 0.50–1.00 | 2.0–3.0 |
| No Travel | ≥ 55 | > 1.00 | > 3.0 |

Load rules:

- Wind ≥ 35 mph with a load over 40,000 lb is at least **Severe**.
- Wind ≥ 45 mph with a load over 30,000 lb is **No Travel**.

### Route ranking

Each checkpoint stands for the stretch of road around it (half the distance to each neighbouring
checkpoint), so miles add up to the route length. Routes are ranked by:

1. fewest No Travel miles
2. fewest Severe miles
3. fewest High miles
4. lowest mile-weighted average risk (Low = 0 … No Travel = 4)
5. shortest travel time

Miles are compared to 0.1 mile and average risk to 0.01, so floating-point noise can't decide a
tie.

## Design decisions and assumptions

**Inputs and units**
- **Range boundaries**: where two table ranges meet, the value goes to the higher level. For
  example, 0.25 in/hr of rain is High. No Travel for rain and snow means strictly above the
  Severe range.
- **Wind** uses sustained 10 m wind speed. Gusts are shown in the popup but not scored.
- **Rain** is rain + showers for the hour that contains the ETA. Snow is that hour's snowfall in
  inches.
- **Truck weight**: TomTom gets the gross weight, assuming a 35,000 lb empty tractor-trailer plus
  the load.
- **Departure**: a time in the past is treated as "now". Departures more than 5 days ahead are
  rejected because the forecast doesn't reach the end of a long trip.

**Routing**
- **Alternatives**: TomTom is asked for 2 alternatives. If it returns fewer than 3 distinct
  routes, the backend forces detours through points offset to either side of the direct route,
  and drops any that duplicate an existing route.
- **ETAs** are interpolated from TomTom's per-instruction travel times, so they reflect slower
  urban sections. They don't include driver rest breaks.

**Heatmap**
- The corridor is a grid of points within about 40 miles of any route.
- Grid spacing grows until there are at most 300 points, which keeps a coast-to-coast trip within
  Open-Meteo's free rate limit.
- Shading uses a continuous 0–4 score that never shows a point as safer than its risk level.

**Performance**
- Forecasts are cached for 30 minutes on a 0.1° grid and fetched in batches of 100 locations.
- Routes and geocoding results are cached too. Departure times are rounded to 15 minutes so
  repeat requests reuse the cache.
- Route geometry is simplified before it is sent to the browser.
- When you select a route, only the map paint expressions change; no data is re-uploaded.
- Heatmap playback blends between hours, so it animates smoothly.
- The map and the vendor libraries load in separate chunks.

**Statelessness**
- The API has no database. Set `REDIS_URL` to share the cache across instances; without it, each
  instance keeps an in-memory cache.

## API

All endpoints return JSON. Errors look like `{"detail": "..."}` or a field-error object.

### `GET /api/health/`

Returns `{"status": "ok"}`.

### `GET /api/geocode/?q=Dallas`

Returns `{"results": [{"label", "lat", "lon"}, ...]}`.

### `POST /api/plan/`

```json
{
  "origin": { "lat": 32.78, "lon": -96.8, "label": "Dallas, TX" },
  "destination": { "lat": 39.74, "lon": -104.99, "label": "Denver, CO" },
  "departure": "2026-11-03T08:00:00Z",
  "load_lb": 42000,
  "interval_miles": 25
}
```

The response contains:

- `recommended_route_id` and `recommendation_reason`.
- `routes`, each with:
  - `id`, `rank`, `recommended`;
  - `distance_miles` and `duration_s`;
  - `geometry`, as `[lon, lat]` points;
  - `score`: miles by level, average risk and max level;
  - `checkpoints`, each with mile, position, ETA, weather and risk (level, factor levels,
    drivers).

### `POST /api/heatmap/`

Request:

```json
{ "routes": [[[lon, lat], ...]], "departure": "...", "load_lb": 42000 }
```

The response contains `start`, `hours` (49), `spacing_deg`, `cells` (`[lat, lon]`) and `scores`.
`scores[cell][hour]` is the risk score × 10.

### Status codes

| Code | Meaning |
|---|---|
| 400 | Invalid input, or no route found |
| 502 | An upstream service failed |
| 503 | Rate limited; try again in a minute |

## Stack

| Layer | Tech |
|---|---|
| Frontend | React 19 (Vite), Material UI, MapLibre GL via react-map-gl |
| Backend | Django, Django REST Framework |
| Routing & geocoding | TomTom APIs (truck profile) |
| Weather | Open-Meteo hourly forecast (no key needed) |

## Project layout

```
backend/
  config/            Django settings, URLs, WSGI
  routing/
    services/        TomTom, Open-Meteo and HTTP clients
    risk.py          risk table and load rules
    checkpoints.py   checkpoint sampling and ETAs
    recommendation.py  route scoring, ranking, explanation
    planner.py       /plan orchestration
    heatmap.py       corridor grid and hourly scores
    tests/           pytest suite
frontend/src/
  components/        form, map, heatmap, results UI
  constants/ utils/ hooks/
  api.js             API client
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
pytest                             # run the tests
```

### Frontend

```bash
cd frontend
npm install
npm run dev                        # http://localhost:5173, proxies /api to :8000
```

## Deployment (Vercel)

The API and the frontend are two Vercel projects from the same repository.

1. **API**:
   - Import the repo with **Root Directory** set to `backend`. `backend/vercel.json` runs Django
     as a Python function.
   - Set these environment variables:
     - `DJANGO_SECRET_KEY` (a long random string)
     - `DJANGO_DEBUG=false`
     - `TOMTOM_API_KEY`
     - `CORS_ALLOWED_ORIGINS` (the frontend URL)
2. **Frontend**:
   - Import the repo with **Root Directory** set to `frontend`. Vite is detected automatically.
   - Set `VITE_API_BASE_URL` to the API URL.
3. Check that `https://<api>/api/health/` returns `{"status": "ok"}`.

# 🛰️ SPACE RISK — Hududning kelajakdagi xavfini oldindan aytuvchi AI

AI platform for UzCosmos. It forecasts natural and environmental hazard risk for Uzbekistan's 14 regions
1–25 years ahead, using satellite-derived indices plus an LLM (via OpenRouter).

**Stack:** Django 5 · Django Templates · PostgreSQL (MySQL / SQLite also supported) · OpenRouter · Three.js · Leaflet · Chart.js · Jazzmin admin

## Features
- Register / login / profile pages, with a 3D rotating Earth on the auth screens
- Landing page with an interactive 3D globe: day/night shader, atmosphere, risk beams over Uzbekistan, orbiting satellites. Click a region to forecast it
- Dark / light mode (dark by default, the choice is remembered). The globe, maps and charts all switch with it
- Dashboard with a satellite map, region ranking, national risk profile and your own stats
- Forecast wizard: pick a region on the map, a horizon (1/5/10/25 years), hazard types and extra context, then watch the scanning animation
- Result page with an animated gauge, 3D "risk constellation" towers, a timeline chart, a radar chart (today vs. future), recommendations, and an **AI analyst chat**
- Built-in fallback engine: the app still works with no API key or if OpenRouter fails
- Jazzmin admin panel (dark theme, branded logo, risk badges, chat history)

## Run locally
```bash
python -m venv .venv
.venv\Scripts\activate            # Windows   (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
copy .env.example .env            # then put your OPENROUTER_API_KEY in .env
python manage.py migrate
python manage.py seed             # 14 regions + admin user from .env
python manage.py runserver
```
Open http://127.0.0.1:8000 · Admin: http://127.0.0.1:8000/admin/

## Deploy to Render (free)
1. Push this folder to a GitHub repository.
2. Create a **PostgreSQL** database on Render (free) and copy its *Internal Database URL*.
3. Create a **Web Service** from the repo:
   - **Build Command:** `pip install -r requirements.txt && python manage.py migrate && python manage.py seed && python manage.py collectstatic --noinput`
   - **Start Command:** `gunicorn courier_project.wsgi:application`
4. Environment variables:

| Key | Value |
|---|---|
| `PYTHON_VERSION` | `3.11.9` |
| `SECRET_KEY` | long random string |
| `DEBUG` | `False` |
| `DATABASE_URL` | Render Postgres internal URL |
| `OPENROUTER_API_KEY` | your key |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` (or any OpenRouter model id) |
| `DJANGO_SUPERUSER_USERNAME` / `_EMAIL` / `_PASSWORD` | admin login created by `seed` |

Or use the included `render.yaml` blueprint, which creates the web service and the database together.

> The Django settings package is called `courier_project` so the start command above works unchanged.

## Logo / brand assets
All in `branding/`:
- `logo-mark.svg`: icon (vector, master file)
- `logo.svg` / `logo-light.svg`: full logo with wordmark for dark / light backgrounds
- `logo-mark-1024.png`, `logo-mark-dark-bg.png`: 1024×1024 PNG icon (transparent / dark background)
- `logo-dark-bg.png`, `logo-light-bg.png`: 2400×512 PNG full logo for slides

The website uses copies in `static/img/`.

## Project layout
```
courier_project/   settings, urls, wsgi
accounts/          register, login, profile
risk/              models, views, OpenRouter client (ai.py), fallback engine (engine.py), hazard + region data, seed command
templates/         Django templates
static/            css, js (globe.js, risk3d.js, space-bg.js, map.js, charts.js), vendored three.js + lucide, Earth textures
branding/          logo files
```

"""Gunicorn settings — picked up automatically by `gunicorn space_risk_project.wsgi:application`."""
import os

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
# AI forecasts/translations can take 30–90 s; gunicorn's default 30 s timeout would kill them (502).
timeout = int(os.getenv("GUNICORN_TIMEOUT", "150"))
graceful_timeout = 30
# Threads keep the site responsive while one request waits on OpenRouter (fits Render's free 512 MB).
worker_class = "gthread"
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
threads = int(os.getenv("GUNICORN_THREADS", "4"))
accesslog = "-"
errorlog = "-"

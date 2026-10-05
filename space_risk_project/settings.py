"""SPACE RISK — Django settings."""
import os
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-insecure-key-change-me-in-production")
DEBUG = env_bool("DEBUG", False)

ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = [
    f"https://{h}" for h in ALLOWED_HOSTS if h not in ("localhost", "127.0.0.1", "*")
]

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "accounts",
    "risk",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "space_risk_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "risk.context_processors.site",
            ],
        },
    },
]

WSGI_APPLICATION = "space_risk_project.wsgi.application"

# Database: PostgreSQL / MySQL via DATABASE_URL, SQLite fallback for local dev.
#   postgres://user:pass@host:5432/dbname
#   mysql://user:pass@host:3306/dbname   (requires `pip install mysqlclient`)
DATABASES = {
    "default": dj_database_url.parse(
        os.getenv("DATABASE_URL", "").strip() or f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "uz"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
WHITENOISE_MANIFEST_STRICT = False

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "risk:dashboard"
LOGOUT_REDIRECT_URL = "risk:landing"

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# ---------------------------------------------------------------- OpenRouter
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
OPENROUTER_TIMEOUT = int(os.getenv("OPENROUTER_TIMEOUT", "60"))
SITE_URL = os.getenv("SITE_URL", f"https://{RENDER_EXTERNAL_HOSTNAME}" if RENDER_EXTERNAL_HOSTNAME else "http://localhost:8000")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"risk": {"handlers": ["console"], "level": "INFO"}},
}

# ---------------------------------------------------------------- Jazzmin admin
JAZZMIN_SETTINGS = {
    "site_title": "SPACE RISK Admin",
    "site_header": "SPACE RISK",
    "site_brand": "SPACE RISK",
    "site_logo": "img/logo-mark.svg",
    "login_logo": "img/logo.svg",
    "login_logo_dark": "img/logo.svg",
    "site_logo_classes": "img-circle",
    "site_icon": "img/logo-mark.svg",
    "welcome_sign": "SPACE RISK boshqaruv paneliga xush kelibsiz",
    "copyright": "SPACE RISK · UzCosmos",
    "search_model": ["auth.User", "risk.Prediction", "risk.Region"],
    "topmenu_links": [
        {"name": "Saytga qaytish", "url": "risk:landing", "new_window": False},
        {"name": "Dashboard", "url": "risk:dashboard", "new_window": False},
        {"model": "risk.Prediction"},
    ],
    "show_sidebar": True,
    "navigation_expanded": True,
    "order_with_respect_to": ["risk", "risk.Prediction", "risk.Region", "risk.ChatMessage", "auth"],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user-astronaut",
        "auth.Group": "fas fa-users",
        "risk.Region": "fas fa-map-marked-alt",
        "risk.Prediction": "fas fa-satellite",
        "risk.ChatMessage": "fas fa-comments",
        "accounts.Profile": "fas fa-id-badge",
    },
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",
    "related_modal_active": True,
    "custom_css": "css/admin.css",
    "show_ui_builder": True,
    "changeform_format": "horizontal_tabs",
}

JAZZMIN_UI_TWEAKS = {
    "theme": "darkly",
    "default_theme_mode": "dark",  # admin has its own light/dark switcher
    "navbar": "navbar-dark",
    "sidebar": "sidebar-dark-info",
    "brand_colour": "navbar-dark",
    "accent": "accent-info",
    "navbar_small_text": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_flat_style": True,
    "button_classes": {
        "primary": "btn-info",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

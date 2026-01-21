import os
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent


def _get_data_root() -> Path:
    """
    Determina el data_root usando la misma lógica que el CLI:
    1. Si DIA_DATA_ROOT está definido, usarlo (soberanía explícita)
    2. Si no, usar data global según OS (mismo comportamiento que CLI)
    """
    if os.getenv("DIA_DATA_ROOT"):
        return Path(os.getenv("DIA_DATA_ROOT")).expanduser().resolve()
    
    # Fallback: data global según OS (mismo que CLI)
    if os.name == "nt":  # Windows
        appdata = os.getenv("APPDATA", "")
        if appdata:
            return Path(appdata) / "dia"
        return Path.home() / "AppData" / "Roaming" / "dia"
    elif sys.platform == "darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "dia"
    else:  # Linux y otros Unix
        xdg_data_home = os.getenv("XDG_DATA_HOME", "")
        if xdg_data_home:
            return Path(xdg_data_home) / "dia"
        return Path.home() / ".local" / "share" / "dia"


DATA_ROOT = _get_data_root()

SECRET_KEY = "dia_v0_1_dev_key"
DEBUG = True
ALLOWED_HOSTS: list[str] = ["*"]

INSTALLED_APPS = [
    "corsheaders",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "api",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "dia_server.urls"

TEMPLATES: list[dict[str, object]] = []

WSGI_APPLICATION = "dia_server.wsgi.application"
ASGI_APPLICATION = "dia_server.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

CORS_ALLOW_ALL_ORIGINS = True

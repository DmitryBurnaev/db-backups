import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LOG_DIR = os.getenv("LOG_DIRECTORY", os.path.join(BASE_DIR, "log"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

YANDEX_TOKEN = os.getenv("YANDEX_TOKEN")
YANDEX_BACKUP_DIR = os.getenv("YANDEX_BACKUP_DIR", "/backups/")
LOCAL_BACKUP_DIR = os.getenv("LOCAL_BACKUP_DIR", os.path.join(BASE_DIR, "backups"))
SENTRY_DSN = os.getenv("SENTRY_DSN")

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")

PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "password")
PG_VERSION = os.getenv("PG_VERSION", "9.6.5")
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")


# override global settings
if not os.path.isdir(LOG_DIR):
    os.mkdir(LOG_DIR)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "%(asctime)s [%(levelname)s] [%(name)s:%(lineno)s]: " "%(message)s"}
    },
    "handlers": {
        "default": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": LOG_LEVEL,
            "formatter": "simple",
            "filename": os.path.join(LOG_DIR, "db_backups.log"),
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8",
        },
        "console": {"class": "logging.StreamHandler", "level": LOG_LEVEL, "formatter": "simple"},
    },
    "loggers": {"": {"handlers": ["default", "console"], "level": LOG_LEVEL, "propagate": True}},
}

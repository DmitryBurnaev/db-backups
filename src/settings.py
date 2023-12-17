import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LOG_DIR = os.getenv("LOG_DIR", os.path.join(BASE_DIR, "log"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

LOCAL_BACKUP_DIR = os.getenv("LOCAL_BACKUP_DIR", os.path.join(BASE_DIR, "backups"))
SENTRY_DSN = os.getenv("SENTRY_DSN")

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")

PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD", "password")
PG_DUMP = os.getenv("PG_DUMP", "pg_dump")  # or specific /usr/lib/postgresql/{ver}/pg_dump
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")

S3_REGION_NAME = os.getenv("S3_REGION_NAME")
S3_STORAGE_URL = os.getenv("S3_STORAGE_URL")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_DST_PATH = os.getenv("S3_DST_PATH")

# override global settings
if not os.path.isdir(LOG_DIR):
    os.mkdir(LOG_DIR)

if not os.path.isdir(LOCAL_BACKUP_DIR):
    os.mkdir(LOCAL_BACKUP_DIR)

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

import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

BASE_DIR = Path(os.path.dirname(os.path.dirname(__file__)))
SRC_DIR = BASE_DIR / "src"
LOG_DIR = Path(os.getenv("DB_BACKUP_LOG_DIR", BASE_DIR / "log"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_LEVEL = os.getenv("DB_BACKUP_LOG_LEVEL", "INFO")
SENTRY_DSN = os.getenv("DB_BACKUP_SENTRY_DSN")

MYSQL_HOST = os.getenv("DB_BACKUP_MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("DB_BACKUP_MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("DB_BACKUP_MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("DB_BACKUP_MYSQL_PASSWORD", "password")

PG_USER = os.getenv("DB_BACKUP_PG_USER", "postgres")
PG_PASSWORD = os.getenv("DB_BACKUP_PG_PASSWORD")
PG_DUMP_BIN = os.getenv(
    "DB_BACKUP_PG_DUMP_BIN", "pg_dump"
)  # or specific /usr/lib/postgresql/{ver}/pg_dump
PG_HOST = os.getenv("DB_BACKUP_PG_HOST", "localhost")
PG_PORT = os.getenv("DB_BACKUP_PG_PORT", "5432")

S3_REGION_NAME = os.getenv("DB_BACKUP_S3_REGION_NAME")
S3_STORAGE_URL = os.getenv("DB_BACKUP_S3_STORAGE_URL")
S3_ACCESS_KEY_ID = os.getenv("DB_BACKUP_S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("DB_BACKUP_S3_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("DB_BACKUP_S3_BUCKET_NAME")
S3_DST_PATH = os.getenv("DB_BACKUP_S3_PATH")

# TODO: use with flag --local
LOCAL_PATH = os.getenv("DB_BACKUP_LOCAL_PATH")
TMP_BACKUP_DIR: Path = Path(tempfile.mkdtemp())


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
        # "console": {"class": "logging.StreamHandler", "level": LOG_LEVEL, "formatter": "simple"},
    },
    "loggers": {"": {"handlers": ["default"], "level": LOG_LEVEL, "propagate": True}},
    # "loggers": {"": {"handlers": ["default", "console"], "level": LOG_LEVEL, "propagate": True}},
}

DATE_FORMAT = "%Y-%m-%d"

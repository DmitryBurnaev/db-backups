import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(filename=os.getenv("ENV_FILE", ".env")))

BASE_DIR = Path(os.path.dirname(os.path.dirname(__file__)))
SRC_DIR = BASE_DIR / "src"
LOG_DIR = Path(os.getenv("LOG_PATH", BASE_DIR / "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
SENTRY_DSN = os.getenv("SENTRY_DSN")

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "password")

PG_USER = os.getenv("PG_USER", "postgres")
PG_PASSWORD = os.getenv("PG_PASSWORD")
# common pg_dump's binary or specific /usr/lib/postgresql/{ver}/pg_dump one:
PG_DUMP_BIN = os.getenv("PG_DUMP_BIN", "pg_dump")
PG_HOST = os.getenv("PG_HOST", "localhost")
PG_PORT = os.getenv("PG_PORT", "5432")

S3_REGION_NAME = os.getenv("S3_REGION_NAME")
S3_STORAGE_URL = os.getenv("S3_STORAGE_URL")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_PATH = os.getenv("S3_PATH")

LOCAL_PATH = Path(os.getenv("LOCAL_PATH_IN_CONTAINER") or os.getenv("LOCAL_PATH", "./backups"))
TMP_BACKUP_DIR = Path(tempfile.mkdtemp())

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
    },
    "loggers": {"": {"handlers": ["default"], "level": LOG_LEVEL, "propagate": True}},
}

DATE_FORMAT = "%Y-%m-%d"

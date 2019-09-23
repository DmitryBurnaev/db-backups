import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
LOG_ROOT = os.path.join(BASE_DIR, "log")

YANDEX_TOKEN = '<override your token>'
YANDEX_BACKUP_DIRECTORY = '/backups/'

MYSQL_DATABASES = []
PG_DATABASES = []
DOCKER_PG_DATABASES = []
PG_VERSION = '9.5'
PG_HOST = 'localhost'
PG_PORT = '5432'

# override global settings
from settings_local import *

if not os.path.isdir(LOG_ROOT):
    os.mkdir(LOG_ROOT)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '%(asctime)s [%(levelname)s] [%(name)s:%(lineno)s]: '
                      '%(message)s'
        },
    },
    'handlers': {
        'default': {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "filename": os.path.join(LOG_ROOT, "db_backups.log"),
            "maxBytes": 10485760,
            "backupCount": 20,
            "encoding": "utf8"
        },
    },
    'loggers': {
        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True
        },
    }
}

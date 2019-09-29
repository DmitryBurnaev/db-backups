"""
This module helps to run backup process
    db_name
    handler
keyword arguments:
    --container_name: Name of running container for targer DB
    --yandex: upload to YandexDisk (using `settings.YANDEX_TOKEN` and "yandex-disk-client" lib)

You can get additional information by using:
$ python3 -m src.run --help

"""

import argparse
import logging
from logging import config

from yandex_disk_client.exceptions import *

from src import settings
from src.handlers import backup_mysql, backup_postgres, backup_postgres_from_docker
from src.settings import (LOGGING)
from src.utils import upload_backup

YANDEX_EXCEPTIONS = YaDiskInvalidResultException, YaDiskInvalidStatusException

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

HANDLERS = {
    "mysql": backup_mysql,
    "postgres": backup_postgres,
    "docker_postgres": backup_postgres_from_docker
}


if __name__ == '__main__':

    p = argparse.ArgumentParser()
    p.add_argument('db_name', metavar='Database Name', type=str,
                   help='Database name for backup')
    p.add_argument('handler', metavar='Backup handler', type=str,
                   choices=HANDLERS.keys(),
                   help=f'Required handler for backup ({list(HANDLERS.keys())})')

    p.add_argument('--container', type=str,
                   help='If using docker_* handler. You should define db-source container')
    p.add_argument('--yandex', default=False, action='store_true',
                   help='Send backup to YandexDisk')
    p.add_argument('--yandex_directory', type=str, default=None,
                   help='If using --yandex, you can define this attribute')
    p.add_argument('--local_directory', type=str, default=None,
                   help='Local directory for saving backups')

    args = p.parse_args()
    if "docker" in args.handler and not args.container:
        logger.critical("You should define --container")
        exit(1)

    backup_handler = HANDLERS[args.handler]
    backup_path, backup_full_path = None, None
    local_directory = args.local_directory or settings.LOCAL_BACKUP_DIRECTORY
    try:
        backup_path, backup_full_path = backup_handler(
            args.db_name, local_directory, container_name=args.container
        )
    except Exception as err:
        logger.exception(f'---- [{args.db_name}] BACKUP FAILED!!! ---- \n Error: {err}')
        exit(2)

    if args.yandex:
        upload_backup(args.db_name, backup_path=backup_path, filename=backup_full_path)

    logger.info(f'---- [{args.db_name}] BACKUP SUCCESS ----')

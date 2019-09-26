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

from handlers import backup_mysql, backup_postgres, backup_postgres_from_docker
from settings import (LOGGING)
from utils import upload_backup

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
    p.add_argument('handler', metavar='Dimension Y', type=str,
                   choices=HANDLERS.keys(),
                   help='Required handler for backup')

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

    backup_handler = HANDLERS[args.handler]
    backup_file_path = backup_handler(args.db_name, args.local_directory, container=args.container)

    if args.yandex:
        upload_backup(backup_file_path)

import os
import tempfile
import logging
from logging import config
import shutil

from yandex_disk_client.exceptions import *
from yandex_disk_client.rest_client import YandexDiskClient

from db_backups import backup_mysql_dbs, backup_pg_dbs, backup_pg_from_docker
from settings import (
    YANDEX_TOKEN,
    YANDEX_BACKUP_DIRECTORY,
    MYSQL_DATABASES,
    PG_DATABASES,
    DOCKER_PG_DATABASES,
    LOGGING,
    LOCAL_BACKUP_DIRECTORY)


logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

yandex_exceptions = YaDiskInvalidResultException, YaDiskInvalidStatusException


def create_backups(client: YandexDiskClient):
    temp_dir_path = tempfile.mkdtemp()
    backup_set = (
        (backup_mysql_dbs, MYSQL_DATABASES),
        (backup_pg_dbs, PG_DATABASES),
        (backup_pg_from_docker, DOCKER_PG_DATABASES),
    )

    for backup_handler, databases in backup_set:
        for db_name in databases:
            backup_result = backup_handler(db_name, temp_dir_path)
            if not backup_result:
                logger.error('---- [{}] BACKUP FAILED!!! ---- '.format(db_name))
                continue

            filename, file_path = backup_result
            cloud_directory = create_backup_directory(client, db_name)

            if cloud_directory is not None:
                try:
                    upload_file(client, file_path, os.path.join(cloud_directory, filename))
                except YaDiskInvalidStatusException:
                    logger.exception("Could upload actual backup to YandexDisk")
                    cloud_directory = None

            if not cloud_directory:
                local_backup_path = os.path.join(LOCAL_BACKUP_DIRECTORY, f"{db_name}_{filename}")
                logger.warning(f"Saving backup to local dir: {local_backup_path}")
                shutil.copy(file_path, local_backup_path)

    shutil.rmtree(temp_dir_path, ignore_errors=True)
    return True


if __name__ == '__main__':
    logger.info('---- Start backup process ----')
    ya_client = YandexDiskClient(YANDEX_TOKEN)
    backup_created = create_backups(client=ya_client)
    if not backup_created:
        logger.warning("---- BACKUP WAS FAILED --- ")
        exit(1)

    logger.info('---- SUCCESS ----')




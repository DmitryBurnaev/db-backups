import os
import tempfile
import logging
from logging import config
import shutil
from datetime import datetime

from yandex_disk_client.exceptions import *
from yandex_disk_client.rest_client import YandexDiskClient

from db_backups import backup_mysql_dbs, backup_pg_dbs, backup_pg_from_docker
from settings import (
    YANDEX_TOKEN, 
    YANDEX_BACKUP_DIRECTORY, 
    MYSQL_DATABASES, 
    PG_DATABASES,
    DOCKER_PG_DATABASES,
    LOGGING
)

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

yandex_exceptions = YaDiskInvalidResultException, YaDiskInvalidStatusException


def upload_file(client, src_filename, dst_filename):
    logger.info(
        'Uploading file {} to {} server'.format(src_filename, dst_filename)
    )
    client.upload(src_filename, dst_filename)


def create_backups(client):

    date_str = datetime.now().strftime('%Y-%m-%d')
    folder_name = os.path.join(YANDEX_BACKUP_DIRECTORY, date_str)

    try:
        client.get_directory(folder_name)
    except yandex_exceptions as ex:
        logger.info(
            f"There is not directory {folder_name} on yandex disk. We are going to create this one."
        )
        try:
            client.mkdir(folder_name)
        except yandex_exceptions:
            logger.exception(f"Can not create folder (we will use exists folder)")
            return False

    temp_dir_path = tempfile.mkdtemp()
    backup_set = (
        (backup_mysql_dbs, MYSQL_DATABASES),
        (backup_pg_dbs, PG_DATABASES),
        (backup_pg_from_docker, DOCKER_PG_DATABASES),
    )

    for backup_handler, databases in backup_set:
        for db in databases:
            backup_result = backup_handler(db, temp_dir_path)
            if not backup_result:
                logger.error('[{}] BACKUP FAILED!!!'.format(db))
                continue
            filename, file_path = backup_result
            upload_file(client, file_path, os.path.join(folder_name, filename))

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

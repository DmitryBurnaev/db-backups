# coding=utf-8
import os
import tempfile
import logging
import shutil
from datetime import datetime

from yandex_disk_client.exceptions import *
from yandex_disk_client.rest_client import YandexDiskClient

from db_backups import backup_mysql_dbs, backup_pg_dbs
from settings import YANDEX_TOKEN, YANDEX_BACKUP_DIRECTORY, \
    MYSQL_DATABASES, PG_DATABASES

logger = logging.getLogger('src/run.py')

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
        client.mkdir(folder_name)
    except yandex_exceptions as ex:
        logger.error('Can not create folder (we will use exists folder): '
                     '{}'.format(ex), exc_info=True)

    temp_dir_path = tempfile.mkdtemp()
    for backup_handler, databases in ((backup_mysql_dbs, MYSQL_DATABASES),
                                      (backup_pg_dbs, PG_DATABASES)):
        for db in databases:
            backup_result = backup_handler(db, temp_dir_path)
            if not backup_result:
                logger.error('[{}] BACKUP FAILED!!!'.format(db))
                continue
            filename, file_path = backup_result
            upload_file(client, file_path, os.path.join(folder_name, filename))

    shutil.rmtree(temp_dir_path, ignore_errors=True)


if __name__ == '__main__':
    logging.info('---- Start backup process ----')
    ya_client = YandexDiskClient(YANDEX_TOKEN)
    create_backups(client=ya_client)
    logging.info('---- DONE ----')

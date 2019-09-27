import os
import logging

from yandex_disk_client.exceptions import YaDiskInvalidResultException, YaDiskInvalidStatusException
from yandex_disk_client.rest_client import YandexDiskClient

from src import settings

YANDEX_EXCEPTIONS = YaDiskInvalidResultException, YaDiskInvalidStatusException

logger = logging.getLogger(__name__)


def create_backup_directory(client: YandexDiskClient, db_name: str) -> str:
    directory_name = os.path.join(settings.YANDEX_BACKUP_DIRECTORY, db_name)
    try:
        client.get_directory(directory_name)
    except YANDEX_EXCEPTIONS as ex:
        logger.info(
            f"Hmm.. Seems like there is not directory {directory_name} on yandex disk. "
            f"We are going to create this one."
        )
        try:
            client.mkdir(directory_name)
        except YANDEX_EXCEPTIONS:
            logger.error(
                f"Oops.. Can not create folder "
                f"(we will try to use exists folder [{directory_name}])"
            )

    return directory_name


def upload_backup(db_name: str, src_filename: str, filename: str):
    yandex_client = YandexDiskClient(settings.YANDEX_TOKEN)
    cloud_directory = create_backup_directory(yandex_client, db_name)
    dst_filename = os.path.join(cloud_directory, filename)

    try:
        logger.info('Uploading file {} to {} server'.format(src_filename, dst_filename))
        yandex_client.upload(src_filename, dst_filename)
    except YANDEX_EXCEPTIONS:
        logger.exception("Shit! We could not upload actual backup to YandexDisk")
    else:
        logger.info(f"Great! uploading for [{db_name}] was done!")
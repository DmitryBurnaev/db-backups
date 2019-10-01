import os
import logging
import subprocess
from datetime import datetime

from yandex_disk_client.exceptions import YaDiskInvalidResultException, YaDiskInvalidStatusException
from yandex_disk_client.rest_client import YandexDiskClient

from src import settings

YANDEX_EXCEPTIONS = YaDiskInvalidResultException, YaDiskInvalidStatusException

logger = logging.getLogger(__name__)


class BackupError(Exception):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def __str__(self):
        return f"BackupError: {self.message}"


def create_backup_directory(client: YandexDiskClient, db_name: str) -> str:
    """ Allows to prepare backup directory on YandexDisk """
    directory_name = os.path.join(settings.YANDEX_BACKUP_DIR, db_name)
    try:
        client.get_directory(directory_name)
    except YANDEX_EXCEPTIONS as exc:
        logger.info(
            f"Hmm.. Seems like there is not directory {directory_name} on yandex disk. ({exc})"
            f"We are going to create this one."
        )
        try:
            client.mkdir(directory_name)
        except YANDEX_EXCEPTIONS as exc:
            logger.error(
                f"Oops.. Can not create folder: {exc} "
                f"(we will try to use exists folder [{directory_name}])"
            )
    else:
        logger.info(f"Yandex directory {directory_name} already exists. We will use it.")
    return directory_name


def upload_backup(db_name: str, backup_path: str, filename: str, yandex_directory: str = None):
    """ Allows to upload src_filename to YandexDisk """
    yandex_client = YandexDiskClient(settings.YANDEX_TOKEN)
    yandex_directory = yandex_directory or create_backup_directory(yandex_client, db_name)
    dst_filename = os.path.join(yandex_directory, filename)

    try:
        logger.info("Uploading file {} to {} server".format(backup_path, dst_filename))
        yandex_client.upload(backup_path, dst_filename)
    except YANDEX_EXCEPTIONS:
        logger.exception("Shit! We could not upload actual backup to YandexDisk")
    else:
        logger.info(f"Great! uploading for [{db_name}] was done!")


def call_with_logging(command: str):
    """ Call command, detect error and logging

    :param command: command that need to be called
    :return: True - not found errors. False - errors founded
    :raise `BackupError`

    """

    logger.debug(f"Call command [{command}] ... ")
    po = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE)

    output = po.stderr.read() if po.stderr else b""
    output = output.decode("utf-8")
    output_lower = output.lower()
    if "error" in output_lower or "fail" in output_lower:
        raise BackupError(output)

    elif output:
        logger.debug(output.strip())


def get_filename(db_name: str, prefix: str) -> str:
    """ Allows to get result name of backup file """

    return f"{datetime.now():%Y-%m-%d}.{db_name}.{prefix}-backup.tar.gz"

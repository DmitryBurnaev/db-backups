import mimetypes
import os
import logging
import subprocess
from datetime import datetime
from urllib.parse import urljoin

import boto3
import botocore
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


def upload_to_s3(db_name: str, backup_path: str, filename: str, yandex_directory: str = None):
    """ Allows to upload src_filename to S3 storage """

    session = boto3.session.Session(
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION_NAME,
    )
    s3 = session.client(service_name="s3", endpoint_url=settings.S3_STORAGE_URL)
    mimetype, _ = mimetypes.guess_type(backup_path)
    dst_path = os.path.join(settings.S3_DST_PATH, filename)
    try:
        logger.info("Executing request (upload) to S3:\n %s\n %s", backup_path, dst_path)
        s3.upload_file(
            Filename=backup_path,
            Bucket=settings.S3_BUCKET_NAME,
            Key=dst_path,
            ExtraArgs={"ACL": "read-write", "ContentType": mimetype},
        )

    except botocore.exceptions.ClientError as error:
        logger.exception("Couldn't execute request (upload) to S3: ClientError %s", str(error),)

    except Exception as error:
        logger.exception("Shit! We couldn't execute upload to S3: %s", error)

    else:
        result_url = urljoin(
            settings.S3_STORAGE_URL, os.path.join(settings.S3_BUCKET_NAME, dst_path)
        )
        logger.info("Great! uploading for [%s] was done! \n result: %s", db_name, result_url)


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

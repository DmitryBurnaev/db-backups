import mimetypes
import os
import logging
import subprocess
from datetime import datetime
from urllib.parse import urljoin

import boto3
from botocore import exceptions as s3_exceptions

from src import settings


logger = logging.getLogger(__name__)


class BackupError(Exception):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def __str__(self):
        return f"BackupError: {self.message}"


def upload_to_s3(db_name: str, backup_path: str, filename: str):
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
            ExtraArgs={"ContentType": mimetype},
        )

    except s3_exceptions.ClientError as error:
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

    return output


def get_filename(db_name: str, prefix: str) -> str:
    """ Allows to get result name of backup file """

    return f"{datetime.now():%Y-%m-%d}.{db_name}.{prefix}-backup.tar.gz"

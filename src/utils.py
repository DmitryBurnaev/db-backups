import dataclasses
import os
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import ClassVar
from urllib.parse import urljoin

import boto3
import click
from botocore import exceptions as s3_exceptions

from src import settings
from src.run import logger_ctx

module_logger = logging.getLogger(__name__)


class BackupError(Exception):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def __str__(self):
        return f"BackupError: {self.message}"


def upload_to_s3(db_name: str, backup_path: Path) -> None:
    """Allows to upload src_filename to S3 storage"""
    logger = logger_ctx.get(default=module_logger)
    check_env_variables(
        "S3_STORAGE_URL",
        "S3_ACCESS_KEY_ID",
        "S3_SECRET_ACCESS_KEY",
        "S3_REGION_NAME",
    )
    session = boto3.session.Session(
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        region_name=settings.S3_REGION_NAME,
    )
    s3 = session.client(service_name="s3", endpoint_url=settings.S3_STORAGE_URL)

    dst_path = os.path.join(settings.S3_DST_PATH, backup_path.name)
    try:
        logger.info("Executing request (upload) to S3:\n %s\n %s", backup_path, dst_path)
        s3.upload_file(
            Filename=backup_path,
            Bucket=settings.S3_BUCKET_NAME,
            Key=dst_path,
            # ExtraArgs={"ContentType": mimetype},
        )

    except s3_exceptions.ClientError as error:
        logger.exception(
            "Couldn't execute request (upload) to S3: ClientError %s",
            str(error),
        )

    except Exception as error:
        logger.exception("Shit! We couldn't execute upload to S3: %s", error)

    else:
        result_url = urljoin(
            settings.S3_STORAGE_URL, os.path.join(settings.S3_BUCKET_NAME, dst_path)
        )
        logger.info("Great! uploading for [%s] was done! \n result: %s", db_name, result_url)


def call_with_logging(command: str):
    """
    Call command, detect error and logging

    :param command: command that need to be called
    :return: True - not found errors. False - errors founded
    :raise `BackupError`

    """
    command = command.strip()
    logger = logger_ctx.get(default=module_logger)

    # TODO: replace passwords with '***'
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


def get_filename(db_name: str, suffix: str = "") -> str:
    """Allows to get result name of backup file"""
    now_time = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    return f"{now_time}.{db_name}.backup{suffix}"


def encrypt_file(file_path: Path, encrypt_pass: str) -> Path:
    """Encrypts file by provided path (with openssl)"""
    encrypted_file_path = file_path.with_suffix(f"{file_path.suffix}.enc")
    encrypt_command = (
        f"openssl enc -aes-256-cbc -e -pbkdf2 -pass {encrypt_pass} -in {file_path} "
        f"> {encrypted_file_path}"
    )
    call_with_logging(command=encrypt_command)
    call_with_logging(command=f"rm {file_path}")
    return encrypted_file_path


def decrypt_file(file_path: Path, encrypt_pass: str) -> Path:
    """Decrypts file by provided path (with openssl)"""
    decrypted_file_path = f"{file_path}.dec"
    decrypt_command = (
        f"openssl enc -aes-256-cbc -d -pbkdf2 -pass {encrypt_pass} -in {file_path} "
        f"> {decrypted_file_path}"
    )
    replace_command = f"rm {file_path} && mv {decrypted_file_path} {file_path}"
    call_with_logging(decrypt_command)
    call_with_logging(replace_command)
    return file_path


def check_env_variables(*env_variables) -> None:
    if missed_variables := [
        variable for variable in env_variables if not getattr(settings, variable)
    ]:
        raise BackupError(f"Missing required variables: {tuple(missed_variables)}")


def copy_file(src: Path, dst: Path | str) -> None:
    dest_dir = Path(dst)
    if not dest_dir.exists():
        dest_dir.mkdir(parents=True, exist_ok=True)

    if not dest_dir.is_dir():
        raise BackupError(f"Couldn't copy backup to non-dir path: '{dst}'")

    try:
        call_with_logging(f"cp {src} {dst}")
    except Exception as exc:
        raise BackupError(f"Couldn't copy backup '{dst}': {exc!r}")


def remove_file(file_path: Path):
    logger = logger_ctx.get(default=module_logger)
    try:
        call_with_logging(f"rm {file_path}")
    except Exception as exc:
        logger.warning("Couldn't remove (and skip) file with path: %s: %r ", file_path, exc)


@dataclasses.dataclass
class LoggerContext:
    """Extended logging (standard logging + click echo) with turning-off verbose mode"""

    skip_colors: bool = False
    verbose: bool = False
    logger: logging.Logger = module_logger

    # class settings:
    log_colors: ClassVar[dict] = {
        logging.DEBUG: "black",
        logging.INFO: "green",
        logging.WARNING: "yellow",
        logging.ERROR: "red",
        logging.CRITICAL: "red",
    }

    def debug(self, msg, *args):
        self._log(msg, *args, level=logging.DEBUG)

    def info(self, msg, *args):
        self._log(msg, *args, level=logging.INFO)

    def warning(self, msg, *args):
        self._log(msg, *args, level=logging.WARNING)

    def error(self, msg, *args):
        self._log(msg, *args, level=logging.ERROR)

    def exception(self, msg, *args):
        self._log(msg, *args, level=logging.ERROR, exception=True)

    def critical(self, msg, *args):
        self._log(msg, *args, level=logging.CRITICAL)

    def _log(self, msg: str, *args, level: int = logging.INFO, exception: bool = False):
        """Logs a message to stderr."""

        if not self.verbose and level <= logging.DEBUG:
            return

        echo_msg = f"{logging.getLevelName(level)}: {msg}"
        if args:
            echo_msg %= args

        color = self.log_colors[level]
        if not self.skip_colors:
            echo_msg = click.style(echo_msg, fg=color)

        click.echo(echo_msg, file=sys.stderr)
        self.logger.log(level, msg, *args, exc_info=exception)

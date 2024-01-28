import dataclasses
import os
import logging
import subprocess
import sys
from datetime import datetime
from operator import itemgetter
from pathlib import Path
from typing import ClassVar, TypeVar
from urllib.parse import urljoin

import boto3
import click

from src import settings
from src.constants import ENV_VARS_REQUIRES
from src.run import logger_ctx
from src.settings import DATE_FORMAT

module_logger = logging.getLogger(__name__)
ENCRYPT_PASS = "env:DB_BACKUP_ENCRYPT_PASS"
T = TypeVar("T")


class BackupError(Exception):
    def __init__(self, message: str):
        super().__init__()
        self.message = message

    def __str__(self):
        return f"BackupError: {self.message}"

    __repr__ = __str__


class EncryptBackupError(BackupError):
    """Custom exception for detecting encryption errors"""


class RestoreBackupError(BackupError):
    """Custom exception for restoring logic"""


def upload_to_s3(db_name: str, backup_path: Path) -> None:
    """Allows to upload src_filename to S3 storage"""
    logger = logger_ctx.get(module_logger)
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
        logger.debug("Executing request (upload) to S3:\n %s\n %s", backup_path, dst_path)
        s3.upload_file(
            Filename=backup_path,
            Bucket=settings.S3_BUCKET_NAME,
            Key=dst_path,
        )

    except Exception as exc:
        logger.exception("Couldn't upload result backup to s3")
        raise BackupError(f"Couldn't upload result backup to s3: {exc!r}") from exc

    result_url = urljoin(settings.S3_STORAGE_URL, os.path.join(settings.S3_BUCKET_NAME, dst_path))
    logger.info("[%s] backup uploaded to s3: %s", db_name, result_url)


def download_from_s3_by_date(db_name: str, date: datetime.date) -> Path:
    """Allows to fetch last backup from provided S3 bucket"""
    logger = logger_ctx.get(module_logger)
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
    session.get_available_resources()
    try:
        prefix = date.strftime("%Y-%m-%d")
        list_objects = s3.list_objects_v2(Bucket=settings.S3_BUCKET_NAME, prefix=prefix)
        objects = sorted(list_objects["Contents"], key=itemgetter("Key"), reverse=True)
        print(objects)
        if not objects:
            raise RestoreBackupError(f"No objects in S3 bucket for requested prefix {prefix}")

        file_name = objects[0]["Key"]
        result_path = settings.TMP_BACKUP_DIR / file_name
        logger.debug(
            "Executing request (download) from S3: %s/%s -> %s",
            settings.S3_DST_PATH,
            file_name,
            result_path,
        )
        # TODO: implement downloading logic
        s3.download_file(
            Bucket=settings.S3_BUCKET_NAME,
            Object=settings.S3_DST_PATH / file_name,
            Filename=result_path
        )

    except Exception as exc:
        logger.exception("Couldn't download result backup from s3")
        raise RestoreBackupError(f"Couldn't download result backup from s3: {exc!r}") from exc

    logger.info("[%s] backup downloaded from s3: %s", db_name, result_path)
    return result_path


def call_with_logging(command: str):
    """
    Call command, detect error and logging

    :param command: command that need to be called
    :return: True - not found errors. False - errors founded
    :raise `BackupError`

    """
    command = command.strip()
    logger = logger_ctx.get(module_logger)

    # TODO: replace passwords with '***'
    logger.debug(f"Call command [{command}] ... ")
    po = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE)

    output = po.stderr.read() if po.stderr else b""
    output = output.decode("utf-8")
    output_lower = output.lower().strip()
    if "error" in output_lower or "fail" in output_lower:
        raise BackupError(output.removeprefix("Error: "))

    elif output:
        logger.debug(output)

    return output


def get_filename(db_name: str, suffix: str = "") -> str:
    """Allows to get result name of backup file"""
    now_time = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    return f"{now_time}.{db_name}.backup{suffix}"


def _check_encrypt_vars(function):
    def inner(*args, **kwargs):
        if missed_env_var := check_env_variables(ENCRYPT_PASS.removeprefix("env:")):
            raise EncryptBackupError(f"Missing value for env variable {missed_env_var}")

        return function(*args, **kwargs)

    return inner


@_check_encrypt_vars
def encrypt_file(db_name: str, file_path: Path) -> Path:
    """Encrypts file by provided path (with openssl)"""
    logger = logger_ctx.get(module_logger)
    encrypted_file_path = file_path.with_suffix(f"{file_path.suffix}.enc")

    encrypt_command = (
        f"openssl enc -aes-256-cbc -e -pbkdf2 -pass {ENCRYPT_PASS} -in {file_path} "
        f"> {encrypted_file_path}"
    )
    call_with_logging(command=encrypt_command)
    call_with_logging(command=f"rm {file_path}")
    logger.info("[%s] encryption: backup file encrypted %s", db_name, encrypted_file_path)
    return encrypted_file_path


@_check_encrypt_vars
def decrypt_file(db_name: str, file_path: Path) -> Path:
    """Decrypts file by provided path (with openssl)"""
    logger = logger_ctx.get(module_logger)
    decrypted_file_path = Path(str(file_path).removesuffix(".enc"))
    decrypt_command = (
        f"openssl enc -aes-256-cbc -d -pbkdf2 -pass {ENCRYPT_PASS} -in {file_path} "
        f"> {decrypted_file_path}"
    )
    replace_command = f"rm {file_path} && mv {decrypted_file_path} {file_path}"
    call_with_logging(decrypt_command)
    call_with_logging(replace_command)
    logger.info("[%s] decryption: backup file decrypted %s", db_name, decrypted_file_path)
    return file_path


def check_env_variables(*env_variables, raise_exception: bool = True) -> list[str]:
    missed_variables = []
    for variable in env_variables:
        settings_var = variable.removesuffix("DB_BACKUP_")
        if not any((os.getenv(variable), getattr(settings, settings_var))):
            missed_variables.append(variable)

    if missed_variables:
        if raise_exception:
            raise BackupError(f"Missing required variables: {tuple(missed_variables)}")

    return missed_variables


def copy_file(db_name: str, src: Path, dst: Path | str) -> None:
    if not dst:
        raise BackupError("Couldn't copy backup: destination path cannot be empty")

    logger = logger_ctx.get(module_logger)
    dest_dir = Path(dst)
    if not dest_dir.exists():
        dest_dir.mkdir(parents=True, exist_ok=True)

    if not dest_dir.is_dir():
        raise BackupError(f"Couldn't copy backup to non-dir path: '{dest_dir}'")

    try:
        call_with_logging(f"cp {src} {dest_dir}")
    except Exception as exc:
        raise BackupError(f"Couldn't copy backup from {src} to '{dest_dir}': {exc!r}")
    else:
        logger.info("[%s] backup copied to %s", db_name, dest_dir / src.name)


def remove_file(file_path: Path):
    logger = logger_ctx.get(module_logger)
    try:
        call_with_logging(f"rm {file_path}")
    except Exception as exc:
        logger.warning("Couldn't remove (and skip) file with path: %s: %r ", file_path, exc)


def find_local_file_by_date(db_name: str, date: datetime.date, directory: Path) -> Path:
    """
    Finds the last backup file in the given directory
    """
    logger = logger_ctx.get(module_logger)
    logger.debug("[%s] Finding last backup file in provided dir: %s", db_name, directory)
    date = date.strftime(DATE_FORMAT)

    def validate_backup_file_name(file_name: str) -> bool:
        if file_name.startswith(date):
            return file_name.endswith("tar.gz") or file_name.endswith("tar.gz.enc")

        return False

    dir_files = sorted(filter(validate_backup_file_name, os.listdir(directory)), reverse=True)
    if not dir_files:
        raise RestoreBackupError(f"No backup files found for date {date}")

    result_path = Path(directory) / dir_files[0]
    logger.debug("[%s] Last backup found: %s", db_name, result_path)
    return result_path


@dataclasses.dataclass
class LoggerContext:
    """Extended logging (standard logging + click echo) with turning-off verbose mode"""

    skip_colors: bool = False
    verbose: bool = False
    logger: logging.Logger = module_logger

    # class settings:
    log_colors: ClassVar[dict] = {
        logging.DEBUG: "white",
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


def validate_envar_option(_, param: click.Option, value: T, required_vars: list[str] | None = None) -> T:
    required_vars = required_vars or ENV_VARS_REQUIRES.get(value)
    if value and (missed_vars := check_env_variables(required_vars, raise_exception=False)):
        raise click.UsageError(
            f"Parameter '{param.name}' requires setting values for variables: {missed_vars}"
        )

    return value


def split_option_values(_, param: click.Option, values: str, split_char: str = ",") -> list[str]:
    split_values = [v.strip() for v in values.split(split_char)]
    for value in split_values:
        validate_envar_option(_, param, value)

    return split_values

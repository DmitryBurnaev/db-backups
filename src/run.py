"""
This module helps to run backup process
You can get additional information by using:

$ python3 -m src.run --help

"""
import click
import logging
from logging import config

import sentry_sdk

from src import settings
from src.backup import run_backup
from src.handlers import HANDLERS
from src.utils import colorized_echo

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)


ENCRYPTION_PASS = {
    "env:var_name": "get the password from an environment variable",
    "file:path_name": "get the password from the first line of the file at location",
    "fd:number": "get the password from the file descriptor number",
}

if settings.SENTRY_DSN:
    sentry_sdk.init(settings.SENTRY_DSN)


@click.command()
@click.argument(
    "db",
    metavar="DB_NAME",
    type=str,
)
@click.option(
    "-h", "--handler",
    metavar="BACKUP_HANDLER",
    type=str,
    required=True,
    show_choices=HANDLERS.keys(),
    help=f"Handler, that will be used for backup {tuple(HANDLERS.keys())}",
)
@click.option(
    "-dc", "--docker-container",
    metavar="CONTAINER_NAME",
    type=str,
    help="""
        Name of docker container which should be used for getting dump.
        Required for using docker_* handler
    """,
)
@click.option(
    "-e", "--encrypt",
    is_flag=True,
    flag_value=True,
    help="Turn ON backup's encryption (with openssl)",
)
@click.option(
    "--encrypt-pass",
    type=str,
    metavar="DB_BACKUP_ENCRYPT_PASS",
    default="env:DB_BACKUP_ENCRYPT_PASS",
    show_default=True,
    help=f"""
        Openssl config to provide source of encryption pass: {tuple(ENCRYPTION_PASS.keys())} |
        see details in README.md
    """,
)
@click.option(
    "--s3",
    is_flag=True,
    flag_value=True,
    help="Send backup to S3-like storage (requires DB_BACKUP_S3_* env vars)",
)
@click.option(
    "-l", "--local",
    is_flag=True,
    flag_value=True,
    help="Store backup locally (requires DB_BACKUP_LOCAL_PATH env)",
)
def backup(
    handler: str,
    db: str,
    docker_container: str | None,
    encrypt: bool,
    encrypt_pass: str | None,
    s3: bool,
    local: bool
):
    """Simple program that backups db 'DB_NAME' via specific BACKUP_HANDLER."""
    colorized_echo(handler, db)
    run_backup(
        handler=handler,
        db=db,
        docker_container=docker_container,
        encrypt=encrypt,
        encrypt_pass=encrypt_pass,
        local=local,
        s3=s3,
    )


if __name__ == "__main__":
    backup()

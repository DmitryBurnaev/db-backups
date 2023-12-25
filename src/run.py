"""
This module helps to run backup process
You can get additional information by using:

$ python3 -m src.run --help

"""
import click
import argparse
import logging
from logging import config

import sentry_sdk

from src import settings
from src.backup import run_backup
from src.handlers import HANDLERS

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
@click.option(
    "--handler",
    metavar="BACKUP_HANDLER",
    type=str,
    required=True,
    choices=HANDLERS.keys(),
    help=f"Handler, which will be used for backup {tuple(HANDLERS.keys())}",
)
@click.option(
    "--docker-container",
    metavar="CONTAINER_NAME",
    dest="docker_container",
    type=str,
    help="""
        Name of docker container which should be used for getting dump. 
        Required for using docker_* handler
    """,
)
@click.option(
    "--encrypt",
    default=False,
    action="store_true",
    help="Turn ON backup's encryption (with openssl)",
)
@click.option(
    "--encrypt-pass",
    type=str,
    dest="encrypt_pass",
    metavar="ENCRYPT_PASS",
    default="env:ENCRYPT_PASS",
    help=f"""
        Openssl config to provide source of encryption pass: {tuple(ENCRYPTION_PASS.keys())} | 
        short-details: {ENCRYPTION_PASS} 
    """,
)
@click.option(
    "--s3",
    default=False,
    action="store_true",
    help="Send backup to S3-like storage (required additional env variables)",
)
@click.option(
    "--local", type=str, default=None, help="Local directory for saving backups"
)
def backup(handler, db, docker_container, encrypt, encrypt_pass, s3, local):
    """Simple program that greets NAME for a total of COUNT times."""
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
    #
    # p = argparse.ArgumentParser()
    # p.add_argument("db", metavar="DB_NAME", type=str, help="Database's name for backup")
    #
    # p.add_argument(
    #     "--handler",
    #     metavar="BACKUP_HANDLER",
    #     type=str,
    #     required=True,
    #     choices=HANDLERS.keys(),
    #     help=f"Handler, which will be used for backup {tuple(HANDLERS.keys())}",
    # )
    # p.add_argument(
    #     "--docker-container",
    #     metavar="CONTAINER_NAME",
    #     dest="docker_container",
    #     type=str,
    #     help="""
    #         Name of docker container which should be used for getting dump.
    #         Required for using docker_* handler
    #     """,
    # )
    # p.add_argument(
    #     "--s3",
    #     default=False,
    #     action="store_true",
    #     help="Send backup to S3-like storage (required additional env variables)",
    # )
    # p.add_argument("--local", type=str, default=None, help="Local directory for saving backups")
    # p.add_argument(
    #     "--encrypt",
    #     default=False,
    #     action="store_true",
    #     help="Turn ON backup's encryption (with openssl)",
    # )
    # p.add_argument(
    #     "--encrypt-pass",
    #     type=str,
    #     dest="encrypt_pass",
    #     metavar="ENCRYPT_PASS",
    #     default="env:ENCRYPT_PASS",
    #     help=f"""
    #         Openssl config to provide source of encryption pass: {tuple(ENCRYPTION_PASS.keys())} |
    #         short-details: {ENCRYPTION_PASS}
    #     """,
    # )
    # # p.add_argument(
    # #     "--restore",
    # #     default=False,
    # #     action="store_true",
    # #     help="Run restore logic instead",
    # # )
    # args = p.parse_args()
    #
    # run_backup(
    #     handler=args.handler,
    #     db=args.db,
    #     docker_container=args.docker_container,
    #     encrypt=args.encrypt,
    #     encrypt_pass=args.encrypt_pass,
    #     local=args.local,
    #     s3=args.s3,
    # )

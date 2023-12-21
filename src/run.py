"""
This module helps to run backup process
    db_name
    handler
keyword arguments:
    --container_name: Name of running container for target DB
    --s3: upload to S3-like storage

You can get additional information by using:
$ python3 -m src.run --help

"""

import argparse
import logging
from logging import config

import sentry_sdk

from src import settings
from src.handlers import backup_mysql, backup_postgres, backup_postgres_from_docker
from src.settings import LOGGING
from src.utils import upload_to_s3, encrypt_file

logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

HANDLERS = {
    "mysql": backup_mysql,
    "postgres": backup_postgres,
    "docker_postgres": backup_postgres_from_docker,
}
ENCRYPTION_PASS = {
    "env:var_name": "get the password from an environment variable",
    "file:path_name": "get the password from the first line of the file at location",
    "fd:number": "get the password from the file descriptor number",
}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("db", metavar="DB_NAME", type=str, help="Database's name for backup")

    p.add_argument(
        "--handler",
        metavar="BACKUP_HANDLER",
        type=str,
        required=True,
        choices=HANDLERS.keys(),
        help=f"Handler, which will be used for backup {tuple(HANDLERS.keys())}",
    )
    p.add_argument(
        "--docker-container",
        metavar="CONTAINER_NAME",
        dest="docker_container",
        type=str,
        help="""
            Name of docker container which should be used for getting dump. 
            Required for using docker_* handler
        """
    )
    p.add_argument(
        "--s3",
        default=False,
        action="store_true",
        help="Send backup to S3-like storage (required additional env variables)",
    )
    p.add_argument("--local", type=str, default=None, help="Local directory for saving backups")
    p.add_argument(
        "--encrypt",
        default=False,
        action="store_true",
        help="Turn ON backup's encryption (with openssl)",
    )
    p.add_argument(
        "--encrypt-pass",
        type=str,
        dest="encrypt_pass",
        metavar="ENCRYPT_PASS",
        default="env:var_name",
        help=f"""
            Openssl config to provide source of encryption pass: {tuple(ENCRYPTION_PASS.keys())}
            | short-details: {ENCRYPTION_PASS} 
        """,
        choices=ENCRYPTION_PASS.keys(),
    )

    if settings.SENTRY_DSN:
        sentry_sdk.init(settings.SENTRY_DSN)

    args = p.parse_args()
    if "docker" in args.handler and not args.docker_container:
        logger.critical(f"Using handler '{args.handler}' requires setting '--docker-container' arg")
        exit(1)

    backup_handler = HANDLERS[args.handler]
    backup_full_path, backup_filename = None, None
    local_directory = args.local_directory or settings.LOCAL_BACKUP_DIR
    try:
        logger.info(f"---- [{args.db_name}] BACKUP STARTED ---- ")
        backup_filename, backup_full_path = backup_handler(
            args.db_name, local_directory, container_name=args.container
        )
    except Exception as err:
        logger.exception(f"---- [{args.db_name}] BACKUP FAILED!!! ---- \n Error: {err}")
        exit(2)

    if args.encrypt:
        encrypt_file(file_path=backup_full_path, encrypt_pass=args.encrypt_pass)

    if args.s3:
        upload_to_s3(
            db_name=args.db_name,
            backup_path=backup_full_path,
            filename=backup_filename,
        )

    logger.info(f"---- [{args.db_name}] BACKUP SUCCESS ----")

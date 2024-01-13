import logging
from functools import partial

import click

from src import utils, settings
from src.handlers import HANDLERS
from src.constants import ENCRYPTION_PASS
from src.run import logger_ctx
from src.utils import LoggerContext, validate_envar_option

ENV_VARS_REQUIRES = {
    "s3": (
        "DB_BACKUP_S3_REGION_NAME",
        "DB_BACKUP_S3_STORAGE_URL",
        "DB_BACKUP_S3_ACCESS_KEY_ID",
        "DB_BACKUP_S3_SECRET_ACCESS_KEY",
        "DB_BACKUP_S3_BUCKET_NAME",
        "DB_BACKUP_S3_PATH",
    ),
    "local": ("DB_BACKUP_LOCAL_PATH",),
    "encrypt": ("DB_BACKUP_LOCAL_PATH",),
}
module_logger = logging.getLogger("backup")


@click.command("backup", short_help="Backup DB to chosen storage (S3-like, local)")
@click.argument(
    "db",
    metavar="DB_NAME",
    type=str,
)
@click.option(
    "-h",
    "--handler",
    metavar="BACKUP_HANDLER",
    required=True,
    show_choices=HANDLERS.keys(),
    type=click.Choice(list(HANDLERS.keys())),
    help=f"Handler, that will be used for backup {tuple(HANDLERS.keys())}",
)
@click.option(
    "-dc",
    "--docker-container",
    metavar="CONTAINER_NAME",
    type=str,
    help="""
        Name of docker container which should be used for getting dump.
        Required for using docker_* handler
    """,
)
@click.option(
    "-e",
    "--encrypt",
    is_flag=True,
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
    "-s3",
    "--copy-s3",
    is_flag=True,
    help="Send backup to S3-like storage (requires DB_BACKUP_S3_* env vars)",
    callback=partial(validate_envar_option, required_vars=ENV_VARS_REQUIRES["s3"]),
)
@click.option(
    "-l",
    "--copy-local",
    is_flag=True,
    help="Store backup locally (requires DB_BACKUP_LOCAL_PATH env)",
    callback=partial(validate_envar_option, required_vars=ENV_VARS_REQUIRES["local"]),
)
@click.option("-v", "--verbose", is_flag=True, flag_value=True, help="Enables verbose mode.")
@click.option("--no-colors", is_flag=True, help="Disables colorized output.")
def cli(
    handler: str,
    db: str,
    docker_container: str | None,
    encrypt: bool,
    encrypt_pass: str | None,
    copy_s3: bool,
    copy_local: bool,
    verbose: bool,
    no_colors: bool,
):
    """Shows file changes in the current working directory."""
    logger = LoggerContext(verbose=verbose, skip_colors=no_colors, logger=module_logger)
    logger_ctx.set(logger)

    if "docker" in handler and not docker_container:
        logger.critical("Using handler '%s' requires '--docker-container' argument", handler)
        exit(1)

    try:
        backup_handler = HANDLERS[handler](db, container_name=docker_container, logger=logger)
    except KeyError:
        logger.critical("Unknown handler '%s'", handler)
        exit(1)

    try:
        backup_full_path = backup_handler()

        if encrypt:
            backup_full_path = utils.encrypt_file(
                db_name=db,
                file_path=backup_full_path,
                encrypt_pass=encrypt_pass,
            )

        if copy_local:
            utils.copy_file(db_name=db, src=backup_full_path, dst=settings.LOCAL_PATH)

        if copy_s3:
            utils.upload_to_s3(db_name=db, backup_path=backup_full_path)

    except Exception as exc:
        logger.exception("[%s] BACKUP FAILED\n %r", db, exc)
        exit(2)

    utils.remove_file(backup_full_path)
    logger.info("[%s] BACKUP SUCCESS", db)

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
    "--handler",
    metavar="BACKUP_HANDLER",
    required=True,
    show_choices=HANDLERS.keys(),
    type=click.Choice(list(HANDLERS.keys())),
    help=f"Handler, that will be used for restore: {tuple(HANDLERS.keys())}",
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
    "--decrypt",
    is_flag=True,
    help="Turn ON backup's decryption (with openssl)",
)
@click.option(
    "-s3",
    "--from-s3",
    is_flag=True,
    help="Send backup to S3-like storage (requires DB_BACKUP_S3_* env vars)",
    callback=partial(validate_envar_option, required_vars=ENV_VARS_REQUIRES["s3"]),
)
@click.option(
    "-l",
    "--from-local",
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
    decrypt: bool,
    from_s3: bool,
    from_local: bool,
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

    logger.info("Run restore logic...")
    # TODO: move logic to common

    try:
        if from_local:
            backup_full_path = utils.find_last_file_in_directory(
                db_name=db,
                directory=settings.LOCAL_PATH,
            )
        elif from_s3:
            # TODO: find backup file in s3:
            backup_full_path = utils.upload_to_s3(db_name=db)
        else:
            backup_full_path = ...

        if decrypt:
            backup_full_path = utils.decrypt_file(db_name=db, file_path=backup_full_path)

        backup_handler.restore(backup_full_path)

    except Exception as exc:
        logger.exception("[%s] BACKUP FAILED\n %r", db, exc)
        exit(2)

    utils.remove_file(backup_full_path)
    logger.info("[%s] BACKUP SUCCESS", db)

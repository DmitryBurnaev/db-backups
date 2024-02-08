import logging
from functools import partial

import click

from src import utils, settings
from src.handlers import HANDLERS, BaseHandler
from src.constants import ENV_VARS_REQUIRES, BACKUP_LOCATIONS
from src.run import logger_ctx
from src.utils import LoggerContext, validate_envar_option, split_option_values

module_logger = logging.getLogger("backup")


@click.command("backup", short_help="Backup DB to chosen storage (S3-like, local)")
@click.argument(
    "DB",
    metavar="DB_NAME",
    type=str,
)
@click.option(
    "--from",
    "handler",
    metavar="BACKUP_HANDLER",
    required=True,
    show_choices=HANDLERS.keys(),
    type=click.Choice(list(HANDLERS.keys())),
    help=f"Handler, that will be used for backup {tuple(HANDLERS.keys())}",
)
@click.option(
    "-c",
    "--container",
    metavar="DOCKER_CONTAINER",
    type=str,
    help="""
        Name of docker container which should be used for getting dump.
        Required for using docker_* handler
    """,
)
@click.option(
    "--to",
    "destination",
    metavar="DESTINATION",
    required=True,
    type=click.STRING,
    help=(
        f"Comma separated list of destination places (result backup file will be moved to). "
        f"Possible values: {BACKUP_LOCATIONS}"
    ),
    callback=split_option_values,
)
@click.option(
    "-e",
    "--encrypt",
    is_flag=True,
    help="Turn ON backup's encryption (with openssl)",
)
@click.option("-v", "--verbose", is_flag=True, flag_value=True, help="Enables verbose mode.")
@click.option("--no-colors", is_flag=True, help="Disables colorized output.")
def cli(
    db: str,
    handler: str,
    container: str | None,
    encrypt: bool,
    destination: tuple[str, ...],
    verbose: bool,
    no_colors: bool,
):
    """
    Backups DB from specific container (or service)
    and uploads it to S3 and/or to the local storage.
    """

    logger = LoggerContext(verbose=verbose, skip_colors=no_colors, logger=module_logger)
    logger_ctx.set(logger)

    if "docker" in handler and not container:
        logger.critical("Using handler '%s' requires '--docker-container' argument", handler)
        exit(1)

    try:
        backup_handler: BaseHandler = HANDLERS[handler](db, container_name=container, logger=logger)
    except KeyError:
        logger.critical("Unknown handler '%s'", handler)
        exit(1)

    try:
        backup_full_path = backup_handler.backup()

        if encrypt:
            backup_full_path = utils.encrypt_file(db_name=db, file_path=backup_full_path)

        if "LOCAL" in destination:
            utils.copy_file(db_name=db, src=backup_full_path, dst=settings.LOCAL_PATH)

        if "S3" in destination:
            utils.upload_to_s3(db_name=db, backup_path=backup_full_path)

    except Exception as exc:
        logger.exception("[%s] BACKUP FAILED\n %r", db, exc)
        exit(2)

    utils.remove_file(backup_full_path)
    logger.info("[%s] BACKUP SUCCESS", db)

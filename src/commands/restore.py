"""
Defines run logic for restore handlers
"""

import sys
import datetime
import logging
from pathlib import Path

import click

from src import utils, settings
from src.constants import BACKUP_LOCATIONS, BackupHandler, BackupLocation
from src.handlers import HANDLERS
from src.run import logger_ctx
from src.settings import DATE_FORMAT
from src.utils import LoggerContext, validate_envar_option

module_logger = logging.getLogger("backup")


@click.command("backup", short_help="Backup DB to chosen storage (S3-like, local)")
@click.argument(
    "DB",
    metavar="DB_NAME",
    type=str,
)
@click.option(
    "--from",
    "backup_source",
    metavar="BACKUP_SOURCE",
    required=True,
    show_choices=BACKUP_LOCATIONS,
    callback=validate_envar_option,
    type=click.Choice(BACKUP_LOCATIONS),
    help=f"Source of backup file, that will be used for downloading/copying: {BACKUP_LOCATIONS}",
)
@click.option(
    "-f",
    "--file",
    "source_file",
    metavar="LOCAL_FILE",
    type=str,
    help="Path to the local file to restore (required param for DESTINATION=FILE).",
)
@click.option(
    "--to",
    "handler",
    metavar="RESTORE_HANDLER",
    required=True,
    show_choices=HANDLERS.keys(),
    type=click.Choice(list(HANDLERS.keys())),
    help=f"Handler, that will be used for restore: {tuple(HANDLERS.keys())}",
)
@click.option(
    "-c",
    "--docker-container",
    metavar="CONTAINER_NAME",
    type=str,
    help="Name of docker container which should be used for getting dump.",
)
@click.option(
    "--date",
    metavar="BACKUP_DATE",
    default=datetime.date.today().strftime(DATE_FORMAT),
    type=click.DateTime(formats=[DATE_FORMAT]),
    help=(
        f"Specific date (in ISO format: {DATE_FORMAT}) for restoring backup "
        f"(default: {datetime.date.today().strftime(DATE_FORMAT)})"
    ),
)
@click.option("-v", "--verbose", is_flag=True, flag_value=True, help="Enables verbose mode.")
@click.option("--no-colors", is_flag=True, help="Disables colorized output.")
def cli(
    db: str,
    backup_source: BackupLocation,
    handler: BackupHandler,
    docker_container: str | None,
    date: datetime.date,
    source_file: str | None,
    verbose: bool,
    no_colors: bool,
):
    """
    Prepares provided file (placed on S3 or local storage) and restore it to specified DB
    """
    logger = LoggerContext(verbose=verbose, skip_colors=no_colors, logger=module_logger)
    logger_ctx.set(logger)

    if handler == BackupHandler.PG_CONTAINER and not docker_container:
        logger.critical("Using handler '%s' requires '--docker-container' argument", handler)
        exit(1)

    if backup_source == BackupLocation.FILE and not source_file:
        logger.critical("Using destination 'LOCAL_PATH' requires '--file' argument")
        exit(1)

    try:
        handler_class = HANDLERS[handler]
        restore_handler = handler_class(db, container_name=docker_container, logger=logger)
    except KeyError:
        logger.critical("Unknown handler '%s'", handler)
        exit(1)

    logger.info("Run restore logic...")

    match backup_source:
        case "FILE":
            source_file = Path(source_file)
            if not source_file.exists():
                raise click.FileError("Source file does not exist")

            utils.copy_file(db, src=source_file, dst=settings.TMP_BACKUP_DIR)
            backup_full_path = settings.TMP_BACKUP_DIR / source_file.name

        case "LOCAL":
            backup_full_path = utils.local_file_search_by_date(
                db_name=db,
                date=date,
                directory=settings.LOCAL_PATH,
            )

        case "S3":
            backup_full_path = utils.s3_download(db_name=db, date=date)

        case _:
            logger.critical("Unknown source '%s'", backup_source)
            sys.exit(1)

    try:
        if str(backup_full_path).endswith(".enc"):
            backup_full_path = utils.decrypt_file(db_name=db, file_path=backup_full_path)

        restore_handler.restore(backup_full_path)

    except Exception as exc:
        logger.exception("[%s] RESTORE FAILED: %r", db, exc)
        sys.exit(2)

    utils.remove_file(backup_full_path)
    logger.info("[%s] RESTORE SUCCESS", db)

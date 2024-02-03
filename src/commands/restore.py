import datetime
import logging
from functools import partial

import click

from src import utils, settings
from src.constants import ENV_VARS_REQUIRES
from src.handlers import HANDLERS
from src.run import logger_ctx
from src.settings import DATE_FORMAT
from src.utils import LoggerContext, validate_envar_option, split_option_values

module_logger = logging.getLogger("backup")
BACKUP_SOURCE = ("S3", "LOCAL")


@click.command("backup", short_help="Backup DB to chosen storage (S3-like, local)")
@click.argument(
    "db",
    metavar="DB_NAME",
    type=str,
)
@click.option(
    "-H",
    "--handler",
    # metavar="RESTORE_HANDLER",
    required=True,
    show_choices=HANDLERS.keys(),
    type=click.Choice(list(HANDLERS.keys())),
    help=f"Handler, that will be used for restore: {tuple(HANDLERS.keys())}",
)
@click.option(
    "--source",
    metavar="BACKUP_SOURCE",
    required=True,
    show_choices=BACKUP_SOURCE,
    callback=validate_envar_option,
    type=click.Choice(list(BACKUP_SOURCE)),
    help=f"Source of backup file, that will be used for downloading/copying: {BACKUP_SOURCE}",
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
@click.option("-v", "--verbose", is_flag=True, flag_value=True, help="Enables verbose mode.")
@click.option("--no-colors", is_flag=True, help="Disables colorized output.")
def cli(
    db: str,
    handler: str,
    source: str,
    date: datetime.date,
    docker_container: str | None,
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
        restore_handler = HANDLERS[handler](db, container_name=docker_container, logger=logger)
    except KeyError:
        logger.critical("Unknown handler '%s'", handler)
        exit(1)

    logger.info("Run restore logic...")

    match source:
        case "LOCAL":
            backup_full_path = utils.find_local_file_by_date(
                db_name=db,
                date=date,
                directory=settings.LOCAL_PATH,
            )

        case "S3":
            backup_full_path = utils.download_from_s3_by_date(db_name=db, date=date)

        case _:
            logger.critical("Unknown source '%s'", source)
            exit(1)

    try:
        if str(backup_full_path).endswith(".enc"):
            backup_full_path = utils.decrypt_file(db_name=db, file_path=backup_full_path)

        restore_handler.restore(backup_full_path)

    except Exception as exc:
        logger.exception("[%s] BACKUP FAILED\n %r", db, exc)
        exit(2)

    utils.remove_file(backup_full_path)
    logger.info("[%s] BACKUP SUCCESS", db)

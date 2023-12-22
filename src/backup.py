import logging
from src.handlers import HANDLERS
from src import utils

logger = logging.getLogger(__name__)


def run_backup(
    handler: str,
    db: str,
    docker_container: str | None,
    encrypt: bool,
    encrypt_pass: str,
    local: str | None = None,
    s3: bool = False,
):

    if "docker" in handler and not docker_container:
        logger.critical(f"Using handler '{handler}' requires setting '--docker-container' arg")
        exit(1)

    backup_handler = HANDLERS[handler](db, container_name=docker_container)
    try:
        logger.info(f"---- [{db}] BACKUP STARTED ---- ")
        backup_full_path = backup_handler()
    except Exception as err:
        logger.exception(f"---- [{db}] BACKUP FAILED!!! ---- \n Error: {err}")
        exit(2)

    if encrypt:
        backup_full_path = utils.encrypt_file(file_path=backup_full_path, encrypt_pass=encrypt_pass)

    if local:
        utils.copy_file(backup_full_path, local)

    if s3:
        utils.upload_to_s3(db_name=db, backup_path=backup_full_path,)

    utils.remove_file(backup_full_path)
    logger.info(f"---- [{db}] BACKUP SUCCESS ----")

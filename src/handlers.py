import os
import logging
from datetime import datetime
from typing import Optional, Tuple

from src import settings
from src.utils import call_with_logging, get_filename, BackupError

logger = logging.getLogger(__name__)
ARCHIVE_COMMAND = "tar -cvzf {backup_full_path} {tmp_filename}"
ARCHIVE_ENCR_COMMAND = (
    "tar -cvzf {backup_full_path} "
    "| openssl enc -aes-256-cbc -pbkdf2 -iter 10000 -e > {tmp_filename}"
)
CLEAN_DIR_COMMAND = "rm {tmp_filename}"


def backup_mysql(db_name: str, target_path: str, **_) -> tuple[str, str] | None:
    """ Backup mysql from mysql server (via mysqldump) """

    logger.info(f"Backup [mysql] {db_name} ... ")
    if not all(
        [settings.MYSQL_USER, settings.MYSQL_PASSWORD, settings.MYSQL_HOST, settings.MYSQL_PORT]
    ):
        logger.critical("You should define MYSQL_* specific fields in ENV")
        return None

    backup_filename = get_filename(db_name, prefix="mysql")
    backup_full_path = os.path.join(target_path, backup_filename)
    tmp_filename = f"/tmp/mysql_backup_{db_name}_{datetime.now().timestamp()}.sql"

    command = (
        f"mysqldump -P {settings.MYSQL_PORT} -h {settings.MYSQL_HOST} -u {settings.MYSQL_USER} "
        f'-p"{settings.MYSQL_PASSWORD}" {db_name} > '
        f"{tmp_filename} && tar -cvzf {backup_full_path} {tmp_filename} && rm {tmp_filename}"
    )
    call_with_logging(command=command)
    logger.info("Backup {}: Success!".format(db_name))
    return backup_filename, backup_full_path


def backup_postgres(db_name: str, target_path: str, encrypt: bool = False, **_) -> tuple[str, str] | None:
    """ Backup PG database from postgres server (via pg_dump) """

    logger.info(f"Backup [postgres]  {db_name} ... ")

    if not all(
        [
            settings.PG_DUMP,
            settings.PG_HOST,
            settings.PG_PORT,
            settings.PG_USER,
            settings.PG_PASSWORD,
        ]
    ):
        logger.critical("You should define PG_* specific fields in ENV")
        return None

    backup_filename = get_filename(db_name, prefix="postgres")
    backup_full_path = os.path.join(target_path, backup_filename)

    command_kwargs = {
        "pg_dump": settings.PG_DUMP,
        "host": settings.PG_HOST,
        "port": settings.PG_PORT,
        "user": settings.PG_USER,
        "password": settings.PG_PASSWORD,
        "db_name": db_name,
        "backup_full_path": backup_full_path,
        "tmp_filename": f"{db_name}.sql",
    }

    pg_dump_command = (
        'PGPASSWORD="{password}" '
        "{pg_dump} -h {host} -p {port} -U {user} -d {db_name} -f {tmp_filename}"
    ).format(**command_kwargs)
    if encrypt:
        archive_command = ARCHIVE_ENCR_COMMAND.format(**command_kwargs)
    else:
        archive_command = ARCHIVE_COMMAND.format(**command_kwargs)

    clean_command = CLEAN_DIR_COMMAND.format(**command_kwargs)

    command = (
        f"{pg_dump_command} && "
        f"{archive_command} && "
        f"{clean_command}"
    )
    stdout = call_with_logging(command=command)
    if not os.path.exists(backup_full_path):
        raise BackupError(f"Backup wasn't created (result file not found). \n{stdout}")

    logger.info("Backup {}: Success!".format(db_name))
    return backup_filename, backup_full_path


def backup_postgres_from_docker(db_name, target_path, container_name) -> Optional[Tuple[str, str]]:
    """Allows to backup postgres db from docker-based postgres server """

    logger.info(f"Backup [docker-postgres] {db_name} ... ")

    backup_filename = get_filename(db_name, prefix="postgres")
    backup_result_path = os.path.join(target_path, backup_filename)
    backup_in_container_path = f"/tmp/{db_name}.tar.gz"

    command_kwargs = {
        "db_name": db_name,
        "backup_full_path": backup_in_container_path,
        "tmp_filename": f"/tmp/{db_name}.sql",
    }
    pg_dump_command = "pg_dump -f {tmp_filename} -d {db_name} -U postgres ".format(**command_kwargs)
    archive_command = ARCHIVE_COMMAND.format(**command_kwargs)
    clean_command = CLEAN_DIR_COMMAND.format(**command_kwargs)

    sh_command = (
        f"{pg_dump_command} && "
        f"{archive_command} && "
        f"{clean_command}"
    )
    docker_command = f'docker exec -t {container_name} sh -c "{sh_command}"'
    copy_file_command = f"docker cp {container_name}:{backup_in_container_path} {backup_result_path}"

    call_with_logging(command=docker_command)
    call_with_logging(command=copy_file_command)

    logger.info("Backup {}: Success!".format(db_name))
    return backup_filename, backup_result_path

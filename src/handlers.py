import os
import logging
from datetime import datetime
from typing import Optional, Tuple

from src import settings
from src.utils import call_with_logging, get_filename

logger = logging.getLogger(__name__)


def backup_mysql(db_name: str, target_path: str, **_) -> Optional[Tuple[str, str]]:
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


def backup_postgres(db_name, target_path, **_) -> Optional[Tuple[str, str]]:
    """ Backup PG database from postgres server (via pg_dump) """

    logger.info(f"Backup [postgres]  {db_name} ... ")

    if not all(
        [
            settings.PG_VERSION,
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
    tmp_filename = f"/tmp/postgres_backup_{db_name}_{datetime.now().timestamp()}.sql"

    command_kwargs = {
        "pg_version": settings.PG_VERSION,
        "host": settings.PG_HOST,
        "port": settings.PG_PORT,
        "user": settings.PG_USER,
        "password": settings.PG_PASSWORD,
        "db_name": db_name,
        "backup_full_path": backup_full_path,
        "tmp_filename": tmp_filename,
    }

    command = (
        'PGPASSWORD="{u_pass}" '
        "/usr/lib/postgresql/{pg_version}/bin/pg_dump -Fc -x -O "
        "-h {host} -p {port} -U {u_name} -d {db_name} > {tmp_filename} "
        "&& tar -cvzf {backup_full_path} {tmp_filename} && rm {tmp_filename}"
    ).format(**command_kwargs)

    call_with_logging(command=command)
    logger.info("Backup {}: Success!".format(db_name))
    return backup_filename, backup_full_path


def backup_postgres_from_docker(db_name, target_path, container_name) -> Optional[Tuple[str, str]]:
    """Allows to backup postgres db from docker-based postgres server """

    logger.info(f"Backup [docker-postgres] {db_name} ... ")

    backup_filename = get_filename(db_name, prefix="postgres")
    backup_full_path = os.path.join(target_path, backup_filename)

    sh_command = (
        f"cd /tmp && pg_dump -f ./{db_name}.sql -d {db_name} -U postgres "
        f"&& tar -cvzf {db_name}.tar.gz {db_name}.sql && rm {db_name}.sql"
    )
    docker_command = f'docker exec -t {container_name} sh -c "{sh_command}"'
    copy_file_command = f"docker cp {container_name}:/tmp/{db_name}.tar.gz {backup_full_path}"

    call_with_logging(command=docker_command)
    call_with_logging(command=copy_file_command)

    logger.info("Backup {}: Success!".format(db_name))
    return backup_filename, backup_full_path

#!/usr/bin/python
import os
import logging
import subprocess
from datetime import datetime

import settings

logger = logging.getLogger(__name__)


def call_with_logging(command, db_name):
    """ Call command, detect error and logging

    :param command: called command
    :param db_name: current db (for logging)
    :return: True - not found errors. False - errors founded
    """
    po = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE)

    output = po.stderr.read() if po.stderr else b''
    output = output.decode('utf-8')
    if 'error' in output:
        logger.error(output)
        return False
    elif output:
        logger.info(output)
    logger.info('Backup {}: Success!'.format(db_name))
    return True


def get_filename(prefix: str) -> str:
    return f'{datetime.now():%Y-%m-%d}.{prefix}-backup.tar.gz'


def backup_mysql(db_name, target_path):
    logger.info(f"Backup [mysql] {db_name} ... ")
    backup_filename = get_filename("mysql")
    backup_full_path = os.path.join(target_path, backup_filename)

    command_kwargs = {
        'u_name': MYSQL_DB_USER,
        'u_pass': MYSQL_DP_PASSWORD,
        'db_name': db_name,
        'file_name': backup_full_path
    }
    command = (
        f"mysqldump -u {settings.MYSQL_USER} -p\"{settings.MYSQL_PASSWORD}\" {db_name}"
        f" | bzip2 > {backup_full_path}"
    )
    # tar -cvzf {db_name}.tar.gz {db_name}.sql && rm {db_name}.sql
    success_result = call_with_logging(command=command, db_name=db_name)
    if not success_result:
        return None

    return backup_filename, backup_full_path


def backup_postgres(db_name, target_path):
    logger.info("Backup {0} ... ".format(db_name))

    if not all([
        settings.PG_VERSION,
        settings.PG_HOST,
        settings.PG_PORT,
        settings.PG_USER,
        settings.PG_PASSWORD,
    ]):
        logger.critical("You should define PG_* specific fields in ENV")
        return None

    backup_filename = '{0}_{1}.backup.bz2'.format(
        datetime.now().strftime('%H%M%S'), db_name
    )
    backup_full_path = os.path.join(target_path, backup_filename)

    command_kwargs = {
        'pg_version': settings.PG_VERSION,
        'host': settings.PG_HOST,
        'port': settings.PG_PORT,
        'u_name': settings.PG_USER,
        'u_pass': settings.PG_PASSWORD,
        'db_name': db_name,
        'file_name': backup_full_path
    }
    command = 'PGPASSWORD="{u_pass}" ' \
              '/usr/lib/postgresql/{pg_version}/bin/pg_dump -Fc -x -O ' \
              '-h {host} -p {port} -U {u_name} -d {db_name} | ' \
              'bzip2 > {file_name}'.format(**command_kwargs)

    success_result = call_with_logging(command=command, db_name=db_name)
    if not success_result:
        return None

    return backup_filename, backup_full_path


def backup_postgres_from_docker(db_name, local_directory, container_name):
    """Allows to backup db from docker-based postgres server """

    logger.info("Backup {0} ... ".format(db_name))
    backup_filename = '{0}.backup.tar.gz'.format(datetime.now().strftime('%Y-%m-%d'))
    local_directory = local_directory or settings.LOCAL_BACKUP_DIRECTORY
    backup_full_path = os.path.join(local_directory, backup_filename)

    sh_command = (
        f"cd /tmp && pg_dump -f ./{db_name}.sql -d {db_name} -U postgres && "
        f"tar -cvzf {db_name}.tar.gz {db_name}.sql && rm {db_name}.sql"
    )
    backup_command = f"docker exec -t postgres sh -c \"{sh_command}\""
    copy_file_command = f"docker cp {container_name}:/tmp/{db_name}.tar.gz {backup_full_path}"

    success_result = call_with_logging(command=backup_command, db_name=db_name)
    if not success_result:
        return

    success_result = call_with_logging(command=copy_file_command, db_name=db_name)
    if not success_result:
        return

    return backup_filename, backup_full_path

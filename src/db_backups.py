#!/usr/bin/python
import os
import logging
import subprocess
from datetime import datetime

from settings import \
    MYSQL_DB_USER, MYSQL_DP_PASSWORD, \
    PG_USER, PG_PASSWORD, PG_VERSION, PG_HOST, PG_PORT

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


def backup_mysql_dbs(db_name, target_path):

    logger.info("Backup {0} ... ".format(db_name))
    backup_filename = '{0}_{1}.mysql.bz2'.format(
        datetime.now().strftime('%H%M%S'), db_name
    )
    backup_full_path = os.path.join(target_path, backup_filename)

    command_kwargs = {
        'u_name': MYSQL_DB_USER,
        'u_pass': MYSQL_DP_PASSWORD,
        'db_name': db_name,
        'file_name': backup_full_path
    }

    command = 'mysqldump -u {u_name} -p"{u_pass}" {db_name} | bzip2 > ' \
              '{file_name}'.format(**command_kwargs)

    success_result = call_with_logging(command=command, db_name=db_name)
    if not success_result:
        return None

    return backup_filename, backup_full_path


def backup_pg_dbs(db_name, target_path):

    logger.info("Backup {0} ... ".format(db_name))
    backup_filename = '{0}_{1}.backup.bz2'.format(
        datetime.now().strftime('%H%M%S'), db_name
    )
    backup_full_path = os.path.join(target_path, backup_filename)

    command_kwargs = {
        'pg_version': PG_VERSION,
        'host': PG_HOST,
        'port': PG_PORT,
        'u_name': PG_USER,
        'u_pass': PG_PASSWORD,
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


def backup_pg_from_docker(db_name, target_path):
    """Allows to backup db from docker-based postgres server """
    
    logger.info("Backup {0} ... ".format(db_name))
    backup_filename = '{0}.backup.tar.gz'.format(datetime.now().strftime('%Y-%m-%d'))
    target_path = target_path or "~/backups/pg_backups/"
    backup_full_path = os.path.join(target_path, backup_filename)

    sh_command = (
        f"cd /tmp && pg_dump -f ./{db_name}.sql -d {db_name} -U postgres && "
        f"tar -cvzf {db_name}.tar.gz {db_name}.sql && rm {db_name}.sql"
    )
    # backup_command = f"docker exec -t postgres-{PG_VERSION} sh -c \"{sh_command}\""
    # copy_file_command = f"docker cp postgres-{PG_VERSION}:/tmp/{db_name}.tar.gz {backup_full_path}"
    backup_command = f"docker exec -t postgres sh -c \"{sh_command}\""
    copy_file_command = f"docker cp postgres:/tmp/{db_name}.tar.gz {backup_full_path}"

    success_result = call_with_logging(command=backup_command, db_name=db_name)
    if not success_result:
        return
    
    success_result = call_with_logging(command=copy_file_command, db_name=db_name)
    if not success_result:
        return
    
    return backup_filename, backup_full_path

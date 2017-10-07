#!/usr/bin/python
import os
import logging
import subprocess
from datetime import datetime

from settings import \
    MYSQL_DB_USER, MYSQL_DP_PASSWORD, \
    PG_USER, PG_PASSWORD, PG_VERSION, PG_HOST, PG_PORT

logger = logging.getLogger('src/db_backups.py')


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

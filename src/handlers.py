import abc
import logging
from abc import ABC
from pathlib import Path
from typing import ClassVar, Type

from src import settings
from src.utils import call_with_logging, get_filename, BackupError, check_env_variables

logger = logging.getLogger(__name__)
# ARCHIVE_COMMAND = "tar -cvzf {compressed_backup_path} {backup_path}"
# CLEAN_COMMAND = "rm {backup_path}"

#
# def backup_mysql(db_name: str, **_) -> Path:
#     """Backup mysql from mysql server (via mysqldump)"""
#
#     logger.info(f"Backup [mysql] {db_name} ... ")
#     check_env_variables(
#         settings.MYSQL_USER,
#         settings.MYSQL_PASSWORD,
#         settings.MYSQL_HOST,
#         settings.MYSQL_PORT,
#     )
#     backup_filename = get_filename(db_name, prefix="mysql")
#     compressed_backup_path = settings.TMP_BACKUP_DIR / backup_filename
#     backup_path = settings.TMP_BACKUP_DIR / f"mysql_bkp_{db_name}_{datetime.now().isoformat()}.sql"
#
#     backup_command = f"""
#         mysqldump -P {settings.MYSQL_PORT} -h {settings.MYSQL_HOST} -u {settings.MYSQL_USER}
#         -p"{settings.MYSQL_PASSWORD}" {db_name} > {backup_path}
#     """
#     archive_command = ARCHIVE_COMMAND.format(
#         compressed_backup_path=compressed_backup_path, backup_path=backup_path
#     )
#     clean_command = CLEAN_COMMAND.format(backup_path=backup_path)
#
#     stdout = call_with_logging(f"{backup_command} && {archive_command} && {clean_command}")
#     if not compressed_backup_path.exists():
#         raise BackupError(f"Backup wasn't created (result file not found). \n{stdout}")
#
#     logger.info(f"Backup [mysql] {db_name}: Success!")
#     return compressed_backup_path
#
#
# def backup_postgres(db_name: str, **_) -> Path:
#     """Backup PG database from postgres server (via pg_dump)"""
#
#     logger.info(f"Backup [postgres] {db_name} ... ")
#     check_env_variables(
#         settings.PG_DUMP_BIN,
#         settings.PG_HOST,
#         settings.PG_PORT,
#         settings.PG_USER,
#         settings.PG_PASSWORD,
#     )
#     backup_filename = get_filename(db_name, prefix="postgres")
#     compressed_backup_path = settings.TMP_BACKUP_DIR / backup_filename
#     backup_path = settings.TMP_BACKUP_DIR / f"pg_bkp_{db_name}_{datetime.now().isoformat()}.sql"
#
#     command_kwargs = {
#         "pg_dump": settings.PG_DUMP_BIN,
#         "host": settings.PG_HOST,
#         "port": settings.PG_PORT,
#         "user": settings.PG_USER,
#         "password": settings.PG_PASSWORD,
#         "db_name": db_name,
#         "compressed_backup_path": compressed_backup_path,
#         "backup_path": backup_path,
#     }
#     backup_command = """
#         PGPASSWORD="{password}" {pg_dump} -h {host} -p {port} -U {user} -d {db_name}
#         -f {backup_path}
#     """.format(
#         **command_kwargs
#     )
#     archive_command = ARCHIVE_COMMAND.format(**command_kwargs)
#     clean_command = CLEAN_COMMAND.format(**command_kwargs)
#
#     stdout = call_with_logging(f"{backup_command} && {archive_command} && {clean_command}")
#     if not compressed_backup_path.exists():
#         raise BackupError(f"Backup wasn't created (result file not found). \n{stdout}")
#
#     logger.info(f"Backup [postgres] {db_name}: Success!")
#     return compressed_backup_path
#
#
# def backup_postgres_from_docker(db_name: str, container_name: str) -> Path:
#     """Allows to backup postgres db from docker-based postgres server"""
#
#     logger.info(f"Backup [docker-postgres] {db_name} ... ")
#
#     backup_filename = get_filename(db_name, prefix="postgres")
#     compressed_backup_path = settings.TMP_BACKUP_DIR / backup_filename
#     backup_path = settings.TMP_BACKUP_DIR / f"pg_bkp_{db_name}_{datetime.now().isoformat()}.sql"
#     backup_in_container_path = f"/tmp/{db_name}.tar.gz"
#
#     command_kwargs = {
#         "db_name": db_name,
#         "compressed_backup_path": compressed_backup_path,
#         "backup_path": backup_path,
#         "backup_in_container_path": backup_in_container_path,
#     }
#     backup_command = "pg_dump -f {backup_in_container_path} -d {db_name} -U postgres ".format(
#         **command_kwargs
#     )
#     archive_command = ARCHIVE_COMMAND.format(**command_kwargs)
#     clean_command = CLEAN_COMMAND.format(**command_kwargs)
#
#     docker_command = f'docker exec -t {container_name} sh -c "{backup_command}"'
#     copy_file_command = f"docker cp {container_name}:{backup_in_container_path} {backup_path}"
#     postprocess_command = f"{archive_command} && {clean_command}"
#
#     call_with_logging(command=docker_command)
#     call_with_logging(command=copy_file_command)
#     call_with_logging(command=postprocess_command)
#
#     logger.info(f"Backup [docker-postgres] {db_name}: Success!")
#     return compressed_backup_path
#


class BaseHandler(ABC):
    service: ClassVar[str] = NotImplemented
    required_variables: ClassVar[tuple[str]] = NotImplemented

    def __init__(self, db_name: str, **extra_kwargs):
        self.db_name = db_name
        self.backup_filename = get_filename(self.db_name)
        self.backup_path = settings.TMP_BACKUP_DIR / f"{self.db_name}.backup.sql"
        self.compressed_backup_path = settings.TMP_BACKUP_DIR / f"{self.backup_filename}.tar.gz"
        self.extra_kwargs = extra_kwargs

    def __call__(self, **kwargs) -> Path:
        logger.info(f"Backup [postgres] {self.db_name} ... ")
        check_env_variables(*self.required_variables)
        backup_stdout = self._do_backup()
        if not self.backup_path.exists():
            raise BackupError(
                f"Backup wasn't created (result file not found). "
                f"\n === \nbackup_stdout: \n{backup_stdout}"
            )

        archive_stdout = self._do_archive()
        if not self.compressed_backup_path.exists():
            raise BackupError(
                f"Backup wasn't archived (result file not found). "
                f"\n === \narchive_stdout: \n{archive_stdout}"
            )

        self._do_clean()

        logger.info(f"Backup [docker-postgres] {self.db_name}: Success!")
        return self.compressed_backup_path

    @abc.abstractmethod
    def _do_backup(self) -> str:
        ...

    def _do_archive(self) -> str:
        parent_dir, file_name = self.backup_path.parent, self.backup_path.name
        command = f"""
            cd {parent_dir} && tar -cvzf {self.compressed_backup_path} {file_name}
        """
        return call_with_logging(command)

    def _do_clean(self) -> str:
        return call_with_logging(command=f"rm {self.backup_path}")


class MySQLHandler(BaseHandler):
    """Backup mysql from mysql server (via mysqldump)"""
    service = "mysql"
    required_variables = (
        "MYSQL_USER",
        "MYSQL_PASSWORD",
        "MYSQL_HOST",
        "MYSQL_PORT",
    )

    def _do_backup(self) -> str:
        command_kwargs = {
            "host": settings.MYSQL_HOST,
            "port": settings.MYSQL_PORT,
            "user": settings.MYSQL_USER,
            "password": settings.MYSQL_PASSWORD,
            "db_name": self.db_name,
            "backup_path": self.backup_path,
        }
        backup_command = """
            mysqldump -P {port} -h {host} -u {user} -p"{password}" {db_name} > {backup_path}
        """
        return call_with_logging(command=backup_command.format(**command_kwargs))


class PGHandler(BaseHandler):
    """Backup PG database from postgres server (via pg_dump)"""

    service = "postgres"
    required_variables = (
        "PG_DUMP_BIN",
        "PG_HOST",
        "PG_PORT",
        "PG_USER",
        "PG_PASSWORD",
    )

    def _do_backup(self) -> str:
        command_kwargs = {
            "pg_dump_bin": settings.PG_DUMP_BIN,
            "host": settings.PG_HOST,
            "port": settings.PG_PORT,
            "user": settings.PG_USER,
            "password": settings.PG_PASSWORD,
            "db_name": self.db_name,
            "backup_path": self.backup_path,
        }
        backup_command = """
            PGPASSWORD="{password}" {pg_dump_bin} -h {host} -p {port} -U {user} -d {db_name} -f {backup_path}    
        """
        return call_with_logging(command=backup_command.format(**command_kwargs))


class DockerPGHandler(BaseHandler):
    service = "docker-postgres"
    required_variables = ()

    def __init__(self, db_name: str, **extra_kwargs):
        super().__init__(db_name, **extra_kwargs)
        self.container_name = self.extra_kwargs.get("container_name")
        if not self.container_name:
            raise RuntimeError("container_name is required")

    def _do_backup(self) -> str:
        """Allows to backup postgres db from docker-based postgres server"""
        backup_in_container_path = f"/tmp/{self.backup_filename}.sql"

        # 1. do backup inside a docker container
        backup_command = self._wrap_do_in_docker(
            f"pg_dump -f {backup_in_container_path} -d {self.db_name} -U postgres"
        )
        stdout = call_with_logging(command=backup_command)

        # 2. copy result file from a docker container to the host machine
        stdout += call_with_logging(
            command=f"docker cp {self.container_name}:{backup_in_container_path} {self.backup_path}"
        )

        # 3. remove tmp file in a docker container
        call_with_logging(command=self._wrap_do_in_docker(f"rm {backup_in_container_path}"))
        return stdout

    def _wrap_do_in_docker(self, command: str) -> str:
        return f'docker exec -t {self.container_name} sh -c "{command}"'


HANDLERS: dict[str, Type[BaseHandler]] = {
    "mysql": MySQLHandler,
    "postgres": PGHandler,
    "docker-postgres": DockerPGHandler,
}

import abc
import logging
from abc import ABC
from pathlib import Path
from typing import ClassVar, Type

import click

from src import settings
from src.constants import BackupHandler
from src.run import logger_ctx
from src.utils import (
    check_env_variables,
    call_with_logging,
    BackupError,
    get_filename,
    RestoreBackupError,
    get_latest_file_by_mask,
)

module_logger = logging.getLogger(__name__)


class BaseHandler(ABC):
    service: ClassVar[str] = NotImplemented
    required_variables: ClassVar[tuple[str]] = NotImplemented

    def __init__(self, db_name: str, **extra_kwargs):
        self.db_name = db_name
        self.logger = logger_ctx.get(module_logger)
        self.backup_filename = get_filename(self.db_name)
        self.backup_path = settings.TMP_BACKUP_DIR / f"{self.db_name}.backup.sql"
        self.compressed_backup_path = settings.TMP_BACKUP_DIR / f"{self.backup_filename}.tar.gz"
        self.extra_kwargs = extra_kwargs

    def backup(self) -> Path:
        self.logger.info("[%s] handle backup via %s ... ", self.db_name, self.service)
        check_env_variables(*self.required_variables)
        backup_stdout = self._do_backup()
        if not self.backup_path.exists():
            raise BackupError(
                f"Backup wasn't created (result file not found). "
                f"\n === \nbackup_stdout: \n{backup_stdout}"
            )

        archive_stdout = self._do_zip()
        if not self.compressed_backup_path.exists():
            raise BackupError(
                f"Backup wasn't archived (result file not found). "
                f"\n === \narchive_stdout: \n{archive_stdout}"
            )

        self._do_clean()

        self.logger.info(
            "[%s] handle backup: success! | file created: %s",
            self.db_name,
            self.compressed_backup_path,
        )
        return self.compressed_backup_path

    def restore(self, file_path: Path) -> None:
        self.logger.info("[%s] handle restore via %s ... ", self.db_name, self.service)
        check_env_variables(*self.required_variables)
        if not file_path.exists():
            raise RestoreBackupError(f"Backup doesn't exist {file_path}")

        self.backup_path = self._do_unzip(file_path)
        self._do_restore(file_path)
        self._do_clean()

    @abc.abstractmethod
    def _do_backup(self) -> str:
        ...

    @abc.abstractmethod
    def _do_restore(self, file_path: Path) -> None:
        ...

    def _do_zip(self) -> str:
        parent_dir, file_name = self.backup_path.parent, self.backup_path.name
        command = f"""
            cd {parent_dir} && tar -cvzf {self.compressed_backup_path} {file_name}
        """
        return call_with_logging(command)

    def _do_unzip(self, compressed_backup_path: Path) -> Path:
        if not compressed_backup_path.name.endswith("tar.gz"):
            self.logger.debug(
                "[%s] backup file %s seems already unzipped (skip unzip process)",
                self.db_name,
                compressed_backup_path,
            )
            return compressed_backup_path

        current_tmp_dir = compressed_backup_path.parent
        call_with_logging(f"tar -zxvf {compressed_backup_path} --directory {current_tmp_dir}")

        if not (result_file := get_latest_file_by_mask(current_tmp_dir, mask="*.sql")):
            raise RestoreBackupError(f"Backup archive doesn't contain any .sql files")

        return result_file

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
        return call_with_logging(
            command=backup_command.format(**command_kwargs),
            password_prefix="-p",
        )

    def _do_restore(self, file_path: Path) -> None:
        raise NotImplementedError("Not implemented yet")


class PGServiceHandler(BaseHandler):
    """Backup PG database from postgres server (via pg_dump)"""

    service = "postgres"
    required_variables = (
        "PG_DUMP_BIN",
        "PG_HOST",
        "PG_PORT",
        "PG_USER",
        "PG_PASSWORD",
    )

    @property
    def command_kwargs(self):
        return {
            "pg_dump_bin": settings.PG_DUMP_BIN,
            "host": settings.PG_HOST,
            "port": settings.PG_PORT,
            "user": settings.PG_USER,
            "password": settings.PG_PASSWORD,
            "db_name": self.db_name,
            "backup_path": self.backup_path,
        }

    def _do_backup(self) -> str:
        backup_command = """
            PGPASSWORD="{password}" {pg_dump_bin} -h{host} -p{port} -U{user} \
            -d {db_name} -f {backup_path}    
        """
        return call_with_logging(
            command=backup_command.format(**self.command_kwargs),
            password_prefix="PGPASSWORD=",
        )

    def _do_restore(self, file_path: Path) -> None:
        if self._check_db_exists():
            msg = (
                f"There is an existing DB on your postgres server. "
                f"Do you want to remove already created DB {self.db_name}?"
            )
            if click.confirm(msg):
                self._drop_db()
            else:
                raise RestoreBackupError("Couldn't restore logic continue during DB exists")

        self._create_db()
        self._restore_db()

    def _check_db_exists(self):
        self.logger.debug("[%s] check DB exists...", self.db_name)
        command = """
            PGPASSWORD="{password}" psql -h{host} -p{port} -U{user} -l | grep {db_name}   
        """
        result = call_with_logging(
            command.format(**self.command_kwargs),
            password_prefix="PGPASSWORD=",
        )
        if exists := result.strip() != "":
            self.logger.debug("[%s] Detected existing DB", self.db_name)

        return exists

    def _drop_db(self):
        self.logger.info("[%s] Removing existing DB...", self.db_name)
        command = """
            PGPASSWORD="{password}" psql -h{host} -p{port} -U{user} \
            -c "DROP DATABASE IF EXISTS {db_name}"  
        """
        call_with_logging(command.format(**self.command_kwargs), password_prefix="PGPASSWORD=")

    def _create_db(self):
        self.logger.info("[%s] Creating new DB...", self.db_name)
        command = """
            PGPASSWORD="{password}" psql -h{host} -p{port} -U{user} \
            -c "CREATE DATABASE {db_name}"  
        """
        call_with_logging(command.format(**self.command_kwargs), password_prefix="PGPASSWORD=")

    def _restore_db(self):
        self.logger.info("[%s] Restoring DB...", self.db_name)
        command = """
            PGPASSWORD="{password}" psql -h{host} -p{port} -U{user} {db_name} < {backup_path}  
        """
        call_with_logging(command.format(**self.command_kwargs), password_prefix="PGPASSWORD=")
        # TODO: check restore error for case: DEBUG: /bin/sh: /var/folders/nh/s3hkf57573953klldrl1nmq40000gn/T/tmpx_fjoun7/v_server_dev410.backup.sql: No such file or directory


class PGDockerHandler(BaseHandler):
    """Backups and restores PG-database inside docker container"""

    service = "postgres-docker"
    required_variables = ()

    def __init__(self, db_name: str, **extra_kwargs):
        super().__init__(db_name, **extra_kwargs)
        self.container_name = self.extra_kwargs.get("container_name")
        if not self.container_name:
            raise RuntimeError("container_name is required")

    def _do_backup(self) -> str:
        """Allows to backup postgres db from docker-based postgres server"""
        backup_in_container_path = f"/tmp/{self.backup_path.name}"

        # 1. do backup inside a docker container
        backup_command = self._wrap_do_in_docker(
            f"pg_dump -f {backup_in_container_path} -d {self.db_name} -U postgres"
        )
        stdout = call_with_logging(command=backup_command)

        # 2. copy result file from a docker container to the host machine
        stdout += call_with_logging(
            f"docker cp {self.container_name}:{backup_in_container_path} {self.backup_path}"
        )

        # 3. remove tmp file in a docker container
        call_with_logging(command=self._wrap_do_in_docker(f"rm {backup_in_container_path}"))
        return stdout

    def _do_restore(self, file_path: Path) -> None:
        if self._check_db_exists():
            msg = (
                f"There is an existing DB on your postgres server. "
                f"Do you want to remove already created DB {self.db_name}?"
            )
            if click.confirm(msg):
                self._drop_db()
            else:
                raise RestoreBackupError("Couldn't restore logic continue during DB exists")

        self._create_db()
        self._restore_db()

    def _check_db_exists(self):
        self.logger.debug("[%s] check DB exists...", self.db_name)
        command = self._wrap_do_in_docker(f"psql  -l | grep {self.db_name}")
        result = call_with_logging(command).strip()
        if exists := result != "0":
            self.logger.debug("[%s] Detected existing DB", self.db_name)

        return exists

    def _drop_db(self):
        self.logger.info("[%s] Removing existing DB...", self.db_name)
        command = self._wrap_psql_in_docker(f"DROP DATABASE IF EXISTS {self.db_name}")
        call_with_logging(command)

    def _create_db(self):
        self.logger.info("[%s] Creating new DB...", self.db_name)
        command = self._wrap_psql_in_docker(f"CREATE DATABASE {self.db_name}")
        call_with_logging(command)

    def _restore_db(self):
        self.logger.info("[%s] Restoring DB...", self.db_name)
        backup_path_in_container = f"/tmp/{self.backup_path.name}"
        call_with_logging(
            f"docker cp {self.backup_path} {self.container_name}:{backup_path_in_container}"
        )
        command = self._wrap_do_in_docker(f"psql {self.db_name} < {backup_path_in_container}")
        call_with_logging(command)

    def _wrap_psql_in_docker(self, command) -> str:
        return self._wrap_do_in_docker(f'psql -c "{command}"')

    def _wrap_do_in_docker(self, command: str) -> str:
        return f'docker exec -t {self.container_name} sh -c "{command}"'


HANDLERS: dict[BackupHandler, Type[BaseHandler]] = {
    BackupHandler.MYSQL: MySQLHandler,
    BackupHandler.PG_SERVICE: PGServiceHandler,
    BackupHandler.PG_CONTAINER: PGDockerHandler,
}
HANDLERS_HUMAN_READABLE: list[str] = [str(handler) for handler in HANDLERS]

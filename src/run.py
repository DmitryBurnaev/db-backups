"""
This module helps to run backup process
You can get additional information by using:

$ python3 -m src.run --help

"""
import click
import logging
from logging import config

import sentry_sdk

from src import settings
from src.backup import run_backup
from src.handlers import HANDLERS
from src.utils import colorized_echo

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)


ENCRYPTION_PASS = {
    "env:var_name": "get the password from an environment variable",
    "file:path_name": "get the password from the first line of the file at location",
    "fd:number": "get the password from the file descriptor number",
}

if settings.SENTRY_DSN:
    sentry_sdk.init(settings.SENTRY_DSN)

#
# @click.command()
# @click.argument(
#     "db",
#     metavar="DB_NAME",
#     type=str,
# )
# @click.option(
#     "-h", "--handler",
#     metavar="BACKUP_HANDLER",
#     type=str,
#     required=True,
#     show_choices=HANDLERS.keys(),
#     help=f"Handler, that will be used for backup {tuple(HANDLERS.keys())}",
# )
# @click.option(
#     "-dc", "--docker-container",
#     metavar="CONTAINER_NAME",
#     type=str,
#     help="""
#         Name of docker container which should be used for getting dump.
#         Required for using docker_* handler
#     """,
# )
# @click.option(
#     "-e", "--encrypt",
#     is_flag=True,
#     flag_value=True,
#     help="Turn ON backup's encryption (with openssl)",
# )
# @click.option(
#     "--encrypt-pass",
#     type=str,
#     metavar="DB_BACKUP_ENCRYPT_PASS",
#     default="env:DB_BACKUP_ENCRYPT_PASS",
#     show_default=True,
#     help=f"""
#         Openssl config to provide source of encryption pass: {tuple(ENCRYPTION_PASS.keys())} |
#         see details in README.md
#     """,
# )
# @click.option(
#     "--s3",
#     is_flag=True,
#     flag_value=True,
#     help="Send backup to S3-like storage (requires DB_BACKUP_S3_* env vars)",
# )
# @click.option(
#     "-l", "--local",
#     is_flag=True,
#     flag_value=True,
#     help="Store backup locally (requires DB_BACKUP_LOCAL_PATH env)",
# )
# def backup(
#     handler: str,
#     db: str,
#     docker_container: str | None,
#     encrypt: bool,
#     encrypt_pass: str | None,
#     s3: bool,
#     local: bool
# ):
#     """Simple program that backups db 'DB_NAME' via specific BACKUP_HANDLER."""
#     colorized_echo(handler, db)
#     run_backup(
#         handler=handler,
#         db=db,
#         docker_container=docker_container,
#         encrypt=encrypt,
#         encrypt_pass=encrypt_pass,
#         local=local,
#         s3=s3,
#     )
#

import os
import sys
import click


CONTEXT_SETTINGS = dict(auto_envvar_prefix="COMPLEX")


class Environment:
    log_colors = {
        logging.DEBUG: "black",
        logging.INFO: "green",
        logging.WARNING: "yellow",
        logging.ERROR: "red",
        logging.CRITICAL: "red",
    }

    def __init__(self):
        self.verbose = False
        self.skip_colours = False
        self.home = os.getcwd()

    def log(self, msg: str, *args, level: int = logging.INFO):
        """Logs a message to stderr."""
        print(self.verbose, level)
        if not self.verbose and level <= logging.DEBUG:
            return

        echo_msg = f"{logging.getLevelName(level)}: {msg}"
        if args:
            echo_msg %= args

        color = self.log_colors[level]
        if not self.skip_colours:
            echo_msg = click.style(echo_msg, fg=color)

        click.echo(echo_msg, file=sys.stderr)
        logger.log(level, msg, *args)

    def vlog(self, msg, *args):
        """Logs a message to stderr only if verbose is enabled."""
        self.log(msg, *args, level=logging.DEBUG)


pass_environment = click.make_pass_decorator(Environment, ensure=True)


class ComplexCLI(click.Group):
    cmd_folder = settings.SRC_DIR / "commands"

    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(self.cmd_folder):
            if filename.endswith(".py"):
                rv.append(filename.replace(".py", ""))

        rv.sort()
        return rv

    def get_command(self, ctx, name):
        try:
            mod = __import__(f"src.commands.{name}", None, None, ["cli"])
        except ImportError:
            return
        return mod.cli


@click.command(cls=ComplexCLI, context_settings=CONTEXT_SETTINGS)
@click.option("-v", "--verbose", is_flag=True, flag_value=True, help="Enables verbose mode.")
@pass_environment
def cli(ctx: Environment, verbose: bool):
    """A complex command line interface."""
    ctx.verbose = verbose
    print("cli", ctx.verbose, id(ctx))


if __name__ == "__main__":
    cli()

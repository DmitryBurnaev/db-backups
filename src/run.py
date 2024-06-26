"""
This module helps to run backup process
You can get additional information by using:

$ python3 -m src.run --help

"""

import os
import logging
import typing
from contextvars import ContextVar
from typing import Callable, Optional

import click
import sentry_sdk

from src import settings

if typing.TYPE_CHECKING:
    from src.utils import LoggerContext

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)
logger_ctx: ContextVar["LoggerContext"] = ContextVar("logger_ctx")

if settings.SENTRY_DSN:
    sentry_sdk.init(settings.SENTRY_DSN)


class ComplexCLI(click.Group):
    """Implements base logic for parsing sub-commands and run it"""

    cmd_folder = settings.SRC_DIR / "commands"

    def list_commands(self, ctx: click.Context):
        """Reads subdirectory 'commands' and adds them to the commands list"""
        rv = []
        for filename in os.listdir(self.cmd_folder):
            if filename.endswith(".py") and not filename.startswith("__"):
                rv.append(filename.replace(".py", ""))

        rv.sort()
        return rv

    def get_command(self, ctx: click.Context, cmd_name: str) -> Optional[Callable]:
        """Imports specific command from src/commands module"""
        try:
            mod = __import__(f"src.commands.{cmd_name}", None, None, ["cli"])
        except ImportError:
            return None

        return mod.cli


@click.command(cls=ComplexCLI)
def cli():
    """A complex command line interface."""


if __name__ == "__main__":
    cli()

"""
This module helps to run backup process
You can get additional information by using:

$ python3 -m src.run --help

"""
import os
import logging
import typing
from logging import config
from contextvars import ContextVar
from typing import Callable, Optional

import click
import sentry_sdk
from dotenv import load_dotenv, find_dotenv

from src import settings

if typing.TYPE_CHECKING:
    from src.utils import LoggerContext

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)
logger_ctx: ContextVar["LoggerContext"] = ContextVar("logger_ctx")
load_dotenv(find_dotenv())

if settings.SENTRY_DSN:
    sentry_sdk.init(settings.SENTRY_DSN)


class ComplexCLI(click.Group):
    cmd_folder = settings.SRC_DIR / "commands"

    def list_commands(self, ctx: click.Context):
        """Reads subdirectory 'commands' and adds them to the commands list"""
        rv = []
        for filename in os.listdir(self.cmd_folder):
            if filename.endswith(".py") and not filename.startswith("__"):
                rv.append(filename.replace(".py", ""))

        rv.sort()
        return rv

    def get_command(self, ctx: click.Context, name: str) -> Optional[Callable]:
        try:
            mod = __import__(f"src.commands.{name}", None, None, ["cli"])
        except ImportError:
            return
        return mod.cli


@click.command(cls=ComplexCLI)
def cli():
    """A complex command line interface."""


if __name__ == "__main__":
    cli()

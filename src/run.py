"""
This module helps to run backup process
You can get additional information by using:

$ python3 -m src.run --help

"""
import os
import logging
from logging import config

import click
import sentry_sdk

from src import settings
from src.utils import LoggerContext

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)
pass_environment = click.make_pass_decorator(LoggerContext, ensure=True)

if settings.SENTRY_DSN:
    sentry_sdk.init(settings.SENTRY_DSN)


class ComplexCLI(click.Group):
    cmd_folder = settings.SRC_DIR / "commands"

    def list_commands(self, ctx):
        rv = []
        for filename in os.listdir(self.cmd_folder):
            if filename.endswith(".py") and not filename.startswith("__"):
                rv.append(filename.replace(".py", ""))

        rv.sort()
        return rv

    def get_command(self, ctx, name):
        try:
            mod = __import__(f"src.commands.{name}", None, None, ["cli"])
        except ImportError:
            return
        return mod.cli


@click.command(cls=ComplexCLI)
@pass_environment
def cli(_: LoggerContext):
    """A complex command line interface."""


if __name__ == "__main__":
    cli()

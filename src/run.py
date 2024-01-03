"""
This module helps to run backup process
You can get additional information by using:

$ python3 -m src.run --help

"""
import os
import logging
from contextvars import ContextVar
from logging import config

import click
import sentry_sdk

from src import settings
from src.utils import LoggerContext

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)
# pass_ = click.make_pass_decorator(LoggerContext, ensure=True)
logger_ctx: ContextVar[LoggerContext] = ContextVar("logger_ctx")


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
@click.option("-v", "--verbose", is_flag=True, flag_value=True, help="Enables verbose mode.")
@click.option("--no-colors", is_flag=True, help="Disables colorized output.")
def cli(verbose: bool, no_colors: bool):
    """A complex command line interface."""
    logger_context = LoggerContext(verbose=verbose, skip_colors=no_colors)
    logger_ctx.set(logger_context)


if __name__ == "__main__":
    cli()

"""
This module helps to run backup process
You can get additional information by using:

$ python3 -m src.run --help

"""
import os
import sys
import logging
from logging import config

import click
import sentry_sdk

from src import settings

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)


if settings.SENTRY_DSN:
    sentry_sdk.init(settings.SENTRY_DSN)


# CONTEXT_SETTINGS = dict(auto_envvar_prefix="COMPLEX")


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
def cli(ctx: Environment):
    """A complex command line interface."""


if __name__ == "__main__":
    cli()

import logging

import click

from src.run import pass_environment


@click.command("backup", short_help="Shows file changes.")
@pass_environment
def cli(ctx):
    """Shows file changes in the current working directory."""
    # ctx.log("Changed files: none")
    print(ctx.verbose, id(ctx))
    ctx.vlog("bla bla bla, debug info")
    ctx.vlog("Call command [%s] ... ", "git clone ...")
    ctx.log("Call command [%s] ... ", "git clone ...", level=logging.DEBUG)
    ctx.log("Call command [%s] ... ", "git clone ...", level=logging.INFO)
    ctx.log("Call command [%s] ... ", "git clone ...", level=logging.WARNING)
    ctx.log("Call command [%s] ... ", "git clone ...", level=logging.ERROR)
    ctx.log("Call command [%s] ... ", "git clone ...", level=logging.CRITICAL)

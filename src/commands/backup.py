import logging

import click

from src.backup import run_backup
from src.handlers import HANDLERS
from src.utils import colorized_echo
from src.run import pass_environment, Environment


@click.command("backup", short_help="Shows file changes.")
@click.argument(
    "db",
    metavar="DB_NAME",
    type=str,
)
@click.option(
    "-h", "--handler",
    metavar="BACKUP_HANDLER",
    type=str,
    required=True,
    show_choices=HANDLERS.keys(),
    help=f"Handler, that will be used for backup {tuple(HANDLERS.keys())}",
)
@click.option(
    "-dc", "--docker-container",
    metavar="CONTAINER_NAME",
    type=str,
    help="""
        Name of docker container which should be used for getting dump.
        Required for using docker_* handler
    """,
)
@click.option(
    "-e", "--encrypt",
    is_flag=True,
    flag_value=True,
    help="Turn ON backup's encryption (with openssl)",
)
@click.option(
    "--encrypt-pass",
    type=str,
    metavar="DB_BACKUP_ENCRYPT_PASS",
    default="env:DB_BACKUP_ENCRYPT_PASS",
    show_default=True,
    help=f"""
        Openssl config to provide source of encryption pass: {tuple(ENCRYPTION_PASS.keys())} |
        see details in README.md
    """,
)
@click.option(
    "--s3",
    is_flag=True,
    flag_value=True,
    help="Send backup to S3-like storage (requires DB_BACKUP_S3_* env vars)",
)
@click.option(
    "-l", "--local",
    is_flag=True,
    flag_value=True,
    help="Store backup locally (requires DB_BACKUP_LOCAL_PATH env)",
)
@pass_environment
def cli(
    ctx: Environment,
    handler: str,
    db: str,
    docker_container: str | None,
    encrypt: bool,
    encrypt_pass: str | None,
    s3: bool,
    local: bool
):
    """Shows file changes in the current working directory."""
    # ctx.log("Changed files: none")
    print(ctx.verbose, id(ctx))
    ctx.vlog("bla bla bla, debug info")
    ctx.vlog("Call command [%s] ... ", "git clone ...")
    colorized_echo(handler, db)
    run_backup(
        handler=handler,
        db=db,
        docker_container=docker_container,
        encrypt=encrypt,
        encrypt_pass=encrypt_pass,
        local=local,
        s3=s3,
    )
    ctx.log("Call command [%s] ... ", "git clone ...", level=logging.DEBUG)
    ctx.log("Call command [%s] ... ", "git clone ...", level=logging.INFO)
    ctx.log("Call command [%s] ... ", "git clone ...", level=logging.WARNING)
    ctx.log("Call command [%s] ... ", "git clone ...", level=logging.ERROR)
    ctx.log("Call command [%s] ... ", "git clone ...", level=logging.CRITICAL)

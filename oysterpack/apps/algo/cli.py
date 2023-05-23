"""
Algorand CLI
"""
import asyncio
from pathlib import Path
from typing import cast

import click

from oysterpack.apps.algo.app import App, AppConfig


@click.group()
def cli():
    """
    Algorand CLI
    """


@cli.group()
@click.option(
    "--config-file",
    required=True,
    prompt="Config File",
    type=click.Path(exists=True, resolve_path=True, readable=True, path_type=Path),
    default="algo.toml",
)
@click.pass_context
def kmd(ctx: click.Context, config_file: Path):
    """
    KMD Client
    """
    app_config = AppConfig.from_config_file(config_file)
    app = App(app_config)
    ctx.obj = app


@kmd.command()
@click.pass_context
def list_wallets(ctx: click.Context):
    app = cast(App, ctx.obj)
    with asyncio.Runner() as runner:
        wallets = runner.run(app.kmd.list_wallets())
    for wallet in sorted(wallets, key=lambda wallet: wallet.name):
        click.echo(wallet)


@kmd.command()
@click.pass_context
def create_wallet(ctx: click.Context):
    app = cast(App, ctx.obj)
    with asyncio.Runner() as runner:

        def get_name() -> str:
            return cast(str, click.prompt("Wallet Name", type=str)).strip()

        while len(name := get_name()) == 0:
            click.echo("Error: wallet name cannot be blank")

        wallets = runner.run(app.kmd.list_wallets())
        while any(wallet.name == name for wallet in wallets):
            click.echo("Error: wallet with the same name already exists")
            while len(name := get_name()) == 0:
                click.echo("Error: wallet name cannot be blank")

        password = cast(
            str,
            click.prompt(
                "Wallet Password",
                value_proc=str.strip,
                hide_input=True,
                confirmation_prompt=True,
            ),
        )

        try:
            runner.run(app.kmd.create_wallet(name, password))
            click.echo("Wallet was successfully created")
        except Exception as err:
            ctx.fail(str(err))


if __name__ == "__main__":
    cli()

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

    async def wallet_exists(name: str) -> bool:
        wallet = await app.kmd.get_wallet(name)
        return wallet is not None

    async def get_name() -> str:
        while (
            len(name := cast(str, click.prompt("Wallet Name", type=str)).strip()) == 0
        ):
            click.echo("Error: wallet name cannot be blank")

        if await wallet_exists(name):
            click.echo("Error: wallet with the same name already exists")
            return await get_name()

        return name

    def get_password() -> str:
        return cast(
            str,
            click.prompt(
                "Wallet Password",
                value_proc=str.strip,
                hide_input=True,
                confirmation_prompt=True,
            ),
        )

    with asyncio.Runner() as runner:
        name = runner.run(get_name())
        password = get_password()
        try:
            runner.run(app.kmd.create_wallet(name, password))
            click.echo("Wallet was successfully created")
        except Exception as err:
            ctx.fail(str(err))


@kmd.command()
@click.pass_context
def recover_wallet(ctx: click.Context):
    """
    Recover a wallet using a master derivation key mnemonic.

    The recovered wallet will be empty. Keys will need to be regenerated.
    """


if __name__ == "__main__":
    cli()

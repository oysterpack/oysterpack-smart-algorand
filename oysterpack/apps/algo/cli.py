"""
Algorand CLI
"""
import asyncio
from enum import IntEnum
from pathlib import Path
from typing import cast

import click

from oysterpack.algorand import Mnemonic
from oysterpack.apps.algo.app import App, AppConfig


@click.group()
def cli():
    """
    Algorand CLI
    """


@cli.group()
def kmd():
    """
    KMD Client
    """


@kmd.group()
@click.option(
    "--config-file",
    required=True,
    prompt="Config File",
    type=click.Path(exists=True, resolve_path=True, readable=True, path_type=Path),
    default="algo.toml",
)
@click.pass_context
def wallets(ctx: click.Context, config_file: Path):
    """
    Wallets
    """
    app_config = AppConfig.from_config_file(config_file)
    app = App(app_config)
    ctx.obj = app


@wallets.command(name="list")
@click.pass_context
def list_wallets(ctx: click.Context):
    """
    List wallets
    """
    app = cast(App, ctx.obj)
    with asyncio.Runner() as runner:
        wallets = runner.run(app.kmd.list_wallets())
    for wallet in sorted(wallets, key=lambda wallet: wallet.name):
        click.echo(wallet)


async def wallet_exists(app: App, name: str) -> bool:
    wallet = await app.kmd.get_wallet(name)
    return wallet is not None


class GetNameMode(IntEnum):
    MustNotExist = 1
    MustExist = 2


async def get_name(app: App, *, mode: GetNameMode = GetNameMode.MustNotExist) -> str:
    while len(name := cast(str, click.prompt("Wallet Name", type=str)).strip()) == 0:
        click.echo("Error: wallet name cannot be blank")

    match mode:
        case GetNameMode.MustNotExist:
            if await wallet_exists(app, name):
                click.echo("Error: wallet with the same name already exists")
                return await get_name(app, mode=mode)
        case GetNameMode.MustExist:
            if not await wallet_exists(app, name):
                click.echo("Error: wallet does not exist")
                return await get_name(app, mode=mode)

    return name


def get_password(*, confirm_password: bool = True) -> str:
    return cast(
        str,
        click.prompt(
            "Wallet Password",
            value_proc=str.strip,
            hide_input=True,
            confirmation_prompt=confirm_password,
        ),
    )


@wallets.command(name="create")
@click.pass_context
def create_wallet(ctx: click.Context):
    """
    Create new wallet
    """
    app = cast(App, ctx.obj)

    with asyncio.Runner() as runner:
        name = runner.run(get_name(app))
        password = get_password()
        try:
            runner.run(app.kmd.create_wallet(name, password))
            click.echo("Wallet was successfully created")
        except Exception as err:
            ctx.fail(str(err))


@wallets.command(name="export-master-derivation-key")
@click.pass_context
def export_wallet_master_derivation_key(ctx: click.Context):
    """
    Exports wallet's master derivation key, which is used to recover the wallet.
    """
    app = cast(App, ctx.obj)

    with asyncio.Runner() as runner:
        name = runner.run(get_name(app, mode=GetNameMode.MustExist))
        password = get_password(confirm_password=False)
        try:
            wallet_session = runner.run(app.kmd.connect(name, password, app.algod))
            mdk = runner.run(wallet_session.export_master_derivation_key())
            click.echo(mdk)
        except Exception as err:
            ctx.fail(str(err))


@wallets.command(name="recover")
@click.pass_context
def recover_wallet(ctx: click.Context):
    """
    Recover a wallet using a master derivation key mnemonic.

    The recovered wallet will be empty. Keys will need to be regenerated.
    """
    app = cast(App, ctx.obj)

    def get_master_derivation_key() -> Mnemonic:
        mdk = cast(
            str,
            click.prompt(
                "Master Derivation Key (Mnemonic)",
                value_proc=str.strip,
                hide_input=True,
            ),
        )
        try:
            return Mnemonic.from_word_list(mdk)
        except Exception as err:
            ctx.fail(f"invalid master derivation key - {err}")

    with asyncio.Runner() as runner:
        name = runner.run(get_name(app))
        password = get_password()
        mdk = get_master_derivation_key()
        try:
            runner.run(app.kmd.recover_wallet(name, password, mdk))
            click.echo("Wallet was successfully recovered")
        except Exception as err:
            ctx.fail(str(err))


@kmd.group()
@click.option(
    "--config-file",
    required=True,
    prompt="Config File",
    type=click.Path(exists=True, resolve_path=True, readable=True, path_type=Path),
    default="algo.toml",
)
@click.pass_context
def accounts(ctx: click.Context, config_file: Path):
    """
    Accounts
    """
    app_config = AppConfig.from_config_file(config_file)
    app = App(app_config)
    ctx.obj = app


@accounts.command(name="list")
@click.pass_context
def list_accounts(ctx: click.Context):
    """
    List wallet accounts
    """
    app = cast(App, ctx.obj)

    with asyncio.Runner() as runner:
        name = runner.run(get_name(app, mode=GetNameMode.MustExist))
        password = get_password(confirm_password=False)
        try:
            wallet_session = runner.run(app.kmd.connect(name, password, app.algod))
            accounts = runner.run(wallet_session.list_accounts())
            for account in sorted(accounts):
                click.echo(account)
        except Exception as err:
            ctx.fail(str(err))


@accounts.command(name="generate")
@click.option("--count", prompt="Count", default=1)
@click.pass_context
def generate_accounts(ctx: click.Context, count: int):
    """
    Generate wallet accounts
    """
    app = cast(App, ctx.obj)

    with asyncio.Runner() as runner:
        name = runner.run(get_name(app, mode=GetNameMode.MustExist))
        password = get_password(confirm_password=False)
        try:
            wallet_session = runner.run(app.kmd.connect(name, password, app.algod))
            for _ in range(count):
                account = runner.run(wallet_session.generate_account())
                click.echo(account)
        except Exception as err:
            ctx.fail(str(err))


if __name__ == "__main__":
    cli()

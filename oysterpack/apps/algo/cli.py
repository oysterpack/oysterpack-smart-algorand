"""
Algorand CLI
"""
import asyncio
from pathlib import Path

import click

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


@kmd.command()
@click.option(
    "--config-file",
    required=True,
    prompt="Config File",
    type=click.Path(exists=True, resolve_path=True, readable=True, path_type=Path),
    default="algo.toml",
)
def list_wallets(config_file: Path):
    app_config = AppConfig.from_config_file(config_file)
    app = App(app_config)
    wallets = asyncio.run(app.list_wallets())
    for wallet in sorted(wallets, key=lambda wallet: wallet.name):
        click.echo(wallet)


if __name__ == "__main__":
    cli()

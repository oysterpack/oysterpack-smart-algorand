"""
Algorand CLI
"""
from pathlib import Path

import click


@click.group()
@click.option(
    "--config-file",
    required=True,
    prompt="Config File",
    type=click.Path(exists=True, resolve_path=True, readable=True, path_type=Path),
)
@click.pass_context
def cli(ctx: click.Context, config_file: Path):
    """
    Algorand CLI
    """
    click.echo(config_file)


@cli.command()
@click.pass_context
def list_wallets(ctx: click.Context):
    click.echo(f"list_wallets: {ctx.obj}")


if __name__ == "__main__":
    cli()

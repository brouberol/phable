import click

from phable.config import config


@click.group(name="config")
def _config():
    """Manage phable config"""


@_config.command(name="show")
def show_config():
    """Display the location of the phable config"""
    click.echo(config.filepath)


@_config.group
def aliases():
    """Manage aliases"""


@aliases.command()
def list():
    """List configured aliases"""
    for name, alias in config.data.get("aliases", {}).items():
        click.echo(f"{name} = {alias}")

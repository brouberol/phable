import atexit

import click

from phable.cache import cache


@click.group(name="cache")
def _cache():
    """Manage internal cache"""


@_cache.command(name="show")
def show_cache():
    """Display the location of the internal phable cache"""
    click.echo(cache.cache_filepath)


@_cache.command()
def clear():
    """Delete the phable internal cache file"""
    cache.clear()
    atexit.unregister(cache.dump)  # avoid re-dumping the in-memory cache back to disk

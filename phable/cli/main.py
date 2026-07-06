import atexit

import click
from click import Context

from phable.cache import cache
from phable.cli.assign import assign_task
from phable.cli.cache import _cache
from phable.cli.comment import comment_on_task
from phable.cli.config import _config
from phable.cli.create import create_task
from phable.cli.list import list_tasks
from phable.cli.move import move_task
from phable.cli.move_project_tasks import move_project_tasks
from phable.cli.parent import parent
from phable.cli.report import report_done_tasks
from phable.cli.set import set_task_fields
from phable.cli.show import show_task
from phable.cli.subscribe import subscribe_to_task
from phable.config import config
from phable.phabricator import PhabricatorClient
from phable.cli._alias import AliasedCommandGroup


@click.group(cls=AliasedCommandGroup)
@click.version_option(package_name="phable-cli")
@click.pass_context
def cli(ctx: Context):
    """Manage Phabricator tasks from the comfort of your terminal"""
    if ctx.invoked_subcommand not in ("cache", "config"):
        ctx.obj = PhabricatorClient(config.phabricator_url, config.phabricator_token)


cli.add_command(assign_task)
cli.add_command(_cache)
cli.add_command(comment_on_task)
cli.add_command(_config)
cli.add_command(create_task)
cli.add_command(move_task)
cli.add_command(move_project_tasks)
cli.add_command(report_done_tasks)
cli.add_command(show_task)
cli.add_command(subscribe_to_task)
cli.add_command(list_tasks)
cli.add_command(parent)
cli.add_command(set_task_fields)


def runcli():
    # Dump the in-memory cache to disk when existing the CLI
    atexit.register(cache.dump)
    cli(max_content_width=120)


if __name__ == "__main__":
    runcli()

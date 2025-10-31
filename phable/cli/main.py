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
from phable.cli.parent import parent
from phable.cli.report import report_done_tasks
from phable.cli.show import show_task
from phable.cli.status import set_task_status
from phable.cli.subscribe import subscribe_to_task
from phable.cli.tag import tag_task
from phable.config import config
from phable.phabricator import PhabricatorClient


class AliasedCommandGroup(click.Group):
    """Custom CLI group allowing the replaement of aliases commands on the fly

    For example if we have the following configuraion:
    [aliases]
    done = move --column 'Done' --milestone

    then calling `phable done T123456` will actually call
    `phable move --column Done --milestone T123456` under the hood.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aliases = config.data.get("aliases", {})

    def make_context(self, info_name, args, parent=None, **extra):
        # First, let's parse the command and handle aliases
        parsed_args = self.parse_command(info_name, args)

        # Then create the context with the possibly modified args
        ctx = super().make_context(
            info_name=parsed_args[0], args=parsed_args[1:], parent=parent, **extra
        )
        return ctx

    def parse_command(self, ctx_name, args):
        """Parse command line arguments and handle aliases"""
        if not args:
            return [ctx_name]

        # Check if the first argument is an alias
        if args[0] in self._aliases:
            pattern = self._aliases[args[0]]
            # Split the pattern and combine with remaining args
            pattern_parts = click.parser.split_arg_string(pattern)
            # Replace the alias with the pattern parts
            args = pattern_parts + args[1:]

        return [ctx_name] + args

    def get_command(self, ctx, cmd_name):
        """Override to handle aliases in command lookup"""
        if cmd_name in self._aliases:
            return super().get_command(ctx, self._aliases[cmd_name].split()[0])
        return super().get_command(ctx, cmd_name)

    def format_help(self, ctx, formatter):
        super().format_help(ctx, formatter)
        if not self._aliases:
            return
        formatter.write("\nAliases:")
        largest_alias = max(map(len, ctx.command.commands.keys()))
        total_spacing = largest_alias + 2
        for alias_name, alias in sorted(self._aliases.items()):
            spacing = " " * (total_spacing - len(alias_name))
            formatter.write(f"\n  {alias_name}{spacing}{alias}")


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
cli.add_command(report_done_tasks)
cli.add_command(show_task)
cli.add_command(subscribe_to_task)
cli.add_command(list_tasks)
cli.add_command(tag_task)
cli.add_command(parent)
cli.add_command(set_task_status)


def runcli():
    # Dump the in-memory cache to disk when existing the CLI
    atexit.register(cache.dump)
    cli(max_content_width=120)


if __name__ == "__main__":
    runcli()

"""
Definition of a mechanism allowing the definition of aliased commands.

For example, the alias "done=move --column 'Done' --milestone` allows the user to type
`phable done T12345` and the actual executed command will be
`phable move --column 'Done' --milestone T12345`

This was inspired by the git aliases, without shell support.

We also hook into click's shell autocomplete, to allow autocomplete options
to be "real" commands or aliased commands, transparently.

"""

import click

from typing import cast

from phable.config import config


class AliasCommand(click.Command):
    def __init__(self, alias, target, group):
        self.alias = alias
        self.target = target
        self.group = group

        super().__init__(
            name=alias,
            callback=lambda: None,  # never called
            help=f"Alias for: {target}",
        )

    def make_context(self, info_name, args, parent=None, **extra):
        pattern = click.parser.split_arg_string(self.target)
        return self.group.make_context(
            info_name,
            pattern + args,
            parent=parent,
            **extra,
        )


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

    def list_commands(self, ctx):
        commands = set(super().list_commands(ctx))
        commands.update(self._aliases)
        return sorted(commands)

    def get_command(self, ctx, cmd_name):
        """Override to handle aliases in command lookup"""
        if cmd_name in self._aliases:
            return AliasCommand(
                cmd_name,
                self._aliases[cmd_name],
                self,
            )

        return super().get_command(ctx, cmd_name)

    def format_help(self, ctx, formatter):
        super().format_help(ctx, formatter)
        if not self._aliases:
            return
        formatter.write("\nAliases:")
        command = cast(AliasedCommandGroup, ctx.command)
        largest_alias = max(map(len, command.commands.keys()))
        total_spacing = largest_alias + 2
        for alias_name, alias in sorted(self._aliases.items()):
            spacing = " " * (total_spacing - len(alias_name))
            formatter.write(f"\n  {alias_name}{spacing}{alias}")

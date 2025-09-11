import click

VARIADIC = -1

project_phid_option = click.option(
    "--project-phid",
    default=None,
    required=False,
    help=(
            "The command will operate on the given project (tag), or to the active "
            "milestone of this project if --milestone is given. If no project "
            "is given, the default project in configuration file is used instead."
    ),
)

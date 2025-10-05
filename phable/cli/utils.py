from typing import Optional

import click

from phable.phabricator import PhabricatorClient

VARIADIC = -1

project_phid_option = click.option(
    "--project",
    default=None,
    required=False,
    help=(
        "The command will operate on the given project (tag), or to the active "
        "milestone of this project if --milestone is given. If no project "
        "is given, the default project in configuration file is used instead."
    ),
)


def find_project_phid_by_title(
    client: PhabricatorClient, ctx: click.Context, project: Optional[str]
) -> Optional[str]:
    if project:
        project_data = client.find_project_by_title(project)
        if not project_data:
            ctx.fail(f"Project {project} not found.")
        return project_data["phid"]
    return None

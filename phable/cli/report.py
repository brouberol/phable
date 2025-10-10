from typing import Optional

import click

from phable.cli.utils import find_project_phid_by_title, project_phid_option
from phable.config import config
from phable.display import TaskFormat, display_tasks
from phable.phabricator import PhabricatorClient


@click.command(name="report-done-tasks")
@project_phid_option
@click.option(
    "--milestone/--no-milestone",
    default=False,
    help=(
        "If --milestone is passed, the task will be moved onto the current project's associated "
        "milestone board, instead of the project board itself"
    ),
)
@click.option(
    "--format",
    type=click.Choice(TaskFormat, case_sensitive=False),
    default="plain",
    help="Output format",
)
@click.option(
    "--source",
    type=str,
    default="Done",
    help="",
)
@click.option(
    "--destination",
    type=str,
    default="Reported",
    help="",
)
@click.pass_context
@click.pass_obj
def report_done_tasks(
    client: PhabricatorClient,
    ctx: click.Context,
    project: Optional[str],
    milestone: bool,
    format: str,
    source: str,
    destination: str,
):
    """
    Print the details of all tasks in the `from` column and move them to the `to` column.

    This is used to produce the weekly reports, and document the tasks as reported once the report is done.
    """
    target_project_phid = client.get_main_project_or_milestone(
        milestone=milestone,
        project_phid=find_project_phid_by_title(client, ctx, project)
        or config.phabricator_default_project_phid,
    )
    column_source_phid = client.find_column_in_project(target_project_phid, source)
    column_destination_phid = client.find_column_in_project(
        target_project_phid, destination
    )
    tasks = client.find_tasks(column_phids=[column_source_phid])

    enriched_tasks = []
    for task in tasks:
        task = client.enrich_task(task)
        enriched_tasks.append(task)
        client.move_task_to_column(task["id"], column_destination_phid)

    display_tasks(enriched_tasks, format=format)

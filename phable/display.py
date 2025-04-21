import json
import click
from typing import Literal, TypeAlias

from .utils import Task

TaskFormat: TypeAlias = Literal["plain", "json"]


def display_task(task: dict, format: TaskFormat):
    if format == "json":
        click.echo(json.dumps(task, indent=2))
    else:
        parent_str = (
            f"{Task.from_int(task['parent']['id'])} - {task['parent']['fields']['name']}"
            if task.get("parent")
            else ""
        )
        click.echo(f"URL: {task['url']}")
        click.echo(f"Task: {Task.from_int(task['id'])}")
        click.echo(f"Title: {task['fields']['name']}")
        if task.get("author"):
            click.echo(f"Author: {task['author']['fields']['username']}")
        if task.get("owner"):
            click.echo(f"Owner: {task['owner']}")
        if task.get("tags"):
            click.echo(f"Tags: {', '.join(task['tags'])}")
        click.echo(f"Status: {task['fields']['status']['name']}")
        click.echo(f"Priority: {task['fields']['priority']['name']}")
        click.echo(f"Description: {task['fields']['description']['raw']}")
        click.echo(f"Parent: {parent_str}")
        click.echo("Subtasks:")
        if task.get("subtasks"):
            for subtask in task["subtasks"]:
                status = f"{'[x]' if subtask['fields']['status']['value'] == 'resolved' else '[ ]'}"
                click.echo(
                    f"{status} - {Task.from_int(subtask['id'])} - @{subtask['owner']:<10} - {subtask['fields']['name']}"
                )


def display_tasks(
    tasks: list[dict],
    format: TaskFormat,
    separator: str = "=" * 50,
):
    if format == "json":
        if len(tasks) == 1:
            display_task(tasks[0], format=format)
        else:
            click.echo(json.dumps(tasks, indent=2))
    else:
        for task in tasks:
            display_task(task, format=format)
            click.echo(separator)

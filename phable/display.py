import json
from typing import Literal, TypeAlias

from .utils import Task

TaskFormat: TypeAlias = Literal["plain", "json", "html", "markdown"]


def display_task(task: dict, format: TaskFormat, prefix: str = "", end: str = "\n"):
    title = f"{Task.from_int(task['id'])} {task['fields']['name']} ({task['fields']['status']['name']})"

    if format == "json":
        print(json.dumps(task, indent=2))
    elif format == "html":
        print(
            f"{prefix}<a href={task['url']}>{title}</a>",
            end=end,
        )
    elif format == "markdown":
        print(
            f"{prefix}[{title}]({task['url']})",
            end=end,
        )
    else:
        parent_str = (
            f"{Task.from_int(task['parent']['id'])} {task['parent']['fields']['name']}"
            if task.get("parent")
            else ""
        )
        print(f"URL: {task['url']}")
        print(f"Task: {Task.from_int(task['id'])}")
        print(f"Title: {task['fields']['name']}")
        if task.get("author"):
            print(f"Author: {task['author']['fields']['username']}")
        if task.get("owner"):
            print(f"Owner: {task['owner']}")
        if task.get("tags"):
            print(f"Tags: {', '.join(task['tags'])}")
        print(f"Status: {task['fields']['status']['name']}")
        print(f"Priority: {task['fields']['priority']['name']}")
        print(f"Description: {task['fields']['description']['raw']}")
        print(f"Parent: {parent_str}")
        print("Subtasks:")
        if task.get("subtasks"):
            for subtask in task["subtasks"]:
                status = f"{'[x]' if subtask['fields']['status']['value'] == 'resolved' else '[ ]'}"
                print(
                    f"{status} - {Task.from_int(subtask['id'])} - @{subtask['owner']:<10} - {subtask['fields']['name']}"
                )


def display_tasks(
    tasks: list[dict],
    format: TaskFormat,
    separator: str = "=" * 50,
):
    if len(tasks) == 1:
        return display_task(tasks[0], format=format)

    if format == "json":
        print(json.dumps(tasks, indent=2))
    elif format == "markdown":
        for task in tasks:
            display_task(task, format=format, prefix="* ")
    else:
        for task in tasks:
            display_task(task, format=format, prefix="<li>", end="")
            print(separator)

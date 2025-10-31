import json
from collections.abc import Callable
from enum import StrEnum, auto

from .task import Task


class TaskFormat(StrEnum):
    PLAIN = auto()
    JSON = auto()
    HTML = auto()
    MARKDOWN = auto()
    WIKITEXT = auto()


def display_tasks(
    tasks: list[dict],
    format: TaskFormat,
) -> None:
    if len(tasks) == 1:
        display_task(tasks[0], format=format)
    get_printer(format).print_list(tasks)


def display_task(task: dict, format: TaskFormat) -> None:
    get_printer(format).print(task)


class TaskPrinter:
    def __init__(self, printer: Callable):
        self._printer = printer

    def print(self, task: dict) -> None:
        pass

    def print_list(self, tasks: list[dict]) -> None:
        pass

    def title(self, task: dict) -> str:
        return f"{Task.from_int(task['id'])} {task['fields']['name']}"

    def status(self, task: dict) -> str:
        return f"({task['fields']['status']['name']})"


class JsonTaskPrinter(TaskPrinter):
    def print(self, task: dict) -> None:
        self._printer(json.dumps(task, indent=2))

    def print_list(self, tasks: list[dict]) -> None:
        self._printer(json.dumps(tasks, indent=2))


class MarkdownTaskPrinter(TaskPrinter):
    def print(self, task: dict) -> None:
        self._printer(f"* [{self.title(task)}]({task['url']}) {self.status(task)}")

    def print_list(self, tasks: list[dict]) -> None:
        for task in tasks:
            self.print(task)


class WikitextTaskPrinter(TaskPrinter):
    def print(self, task: dict) -> None:
        self._printer(f"* [{task['url']} {self.title(task)}] {self.status(task)}")

    def print_list(self, tasks: list[dict]) -> None:
        for task in tasks:
            self.print(task)


class HtmlTaskPrinter(TaskPrinter):
    def print(self, task: dict) -> None:
        self._printer(
            f"<a href={task['url']}>{self.title(task)}</a> {self.status(task)}"
        )

    def print_list(self, tasks: list[dict]) -> None:
        for task in tasks:
            self._printer(
                f"<li><a href={task['url']}>{self.title(task)}</a> {self.status(task)}</li>"
            )


class PlainTaskPrinter(TaskPrinter):
    def print(self, task: dict) -> None:
        parent_str = self.title(task.get("parent")) if task.get("parent") else ""
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

    def print_list(self, tasks: list[dict]) -> None:
        for task in tasks:
            self.print(task)
            self._printer("=" * 50)


def get_printer(format: TaskFormat) -> TaskPrinter:
    if format == TaskFormat.PLAIN:
        return PlainTaskPrinter(print)
    elif format == TaskFormat.JSON:
        return JsonTaskPrinter(print)
    elif format == TaskFormat.HTML:
        return HtmlTaskPrinter(print)
    elif format == TaskFormat.MARKDOWN:
        return MarkdownTaskPrinter(print)
    elif format == TaskFormat.WIKITEXT:
        return WikitextTaskPrinter(print)
    else:
        raise ValueError(f"Unknown format: {format}")

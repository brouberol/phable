from enum import StrEnum

import click


class Task(int):
    @classmethod
    def from_str(cls, value: str) -> int:
        return int(value.lstrip("T"))

    @classmethod
    def from_int(cls, value: int) -> str:
        return f"T{value}"


class TaskParamType(click.ParamType):
    name = "task_id"

    def convert(self, value, param, ctx):
        return Task.from_str(value)


TASK_ID = TaskParamType()


class TaskStatus(StrEnum):
    open = "open"
    resolved = "resolved"
    progress = "progress"
    stalled = "stalled"
    invalid = "invalid"
    declined = "declined"

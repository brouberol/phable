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
    duplicate = "duplicate"


# TODO these are hard-coded for Wikimedia's Phab, we should do something better
class TaskPriority(StrEnum):
    lowest = "lowest"
    low = "low"
    medium = "medium"
    high = "high"
    unbreak = "unbreak"
    triage = "triage"

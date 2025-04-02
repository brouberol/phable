import os
from dataclasses import dataclass, field
from functools import partial

import click

_warnings = []


def os_getenv_or_raise(env_var_name: str):
    if val := os.getenv(env_var_name):
        return val
    _warnings.append(f"Required environment variable {env_var_name} is not set")


def field_with_default_from_env(env_var_name):
    return field(default_factory=partial(os_getenv_or_raise, env_var_name))


@dataclass(frozen=True)
class Config:
    phabricator_url: str = field_with_default_from_env("PHABRICATOR_URL")
    phabricator_token: str = field_with_default_from_env("PHABRICATOR_TOKEN")
    phabricator_default_project_phid: str = field_with_default_from_env(
        "PHABRICATOR_DEFAULT_PROJECT_PHID"
    )

    def __post_init__(self):
        for warn in _warnings:
            click.echo(click.style(warn, fg="yellow"), err=True)
        return len(_warnings) == 0


config = Config()

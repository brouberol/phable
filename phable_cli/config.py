import os
import sys
from configparser import ConfigParser
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path

import click


_warnings = []

CONFIG_HOME_PER_PLATFORM = {
    "darwin": Path.home() / "Library" / "Preferences",
    "linux": Path(os.getenv("XDG_CACHE_HOME", f"{Path.home()}/.config")),
    "windows": Path("c:/", "Users", os.getlogin(), "AppData", "Local", "Programs"),
}
config_filepath = CONFIG_HOME_PER_PLATFORM[sys.platform] / "phable" / "config.ini"


def os_getenv_or_raise(env_var_name: str):
    if val := os.getenv(env_var_name):
        return val
    _warnings.append(f"Required environment variable {env_var_name} is not set")


def field_with_default_from_env(env_var_name):
    return field(default_factory=partial(os_getenv_or_raise, env_var_name))


def read_config() -> dict:
    if not config_filepath.parent.exists():
        config_filepath.parent.mkdir()
    if not config_filepath.exists():
        return {}
    else:
        config = ConfigParser()
        try:
            config.read(config_filepath)
        except Exception:
            _warnings.append(
                f"Configuration file {config_filepath} is invalid. Skipping parsing."
            )
            return {}
        else:
            return {
                section: dict(config.items(section)) for section in config.sections()
            }


@dataclass()
class Config:
    phabricator_url: str = field_with_default_from_env("PHABRICATOR_URL")
    phabricator_token: str = field_with_default_from_env("PHABRICATOR_TOKEN")
    phabricator_default_project_phid: str = field_with_default_from_env(
        "PHABRICATOR_DEFAULT_PROJECT_PHID"
    )
    filepath: Path = field(default=config_filepath)
    data: dict = field(default_factory=read_config)

    def __post_init__(self):
        for warn in _warnings:
            click.echo(click.style(warn, fg="yellow"), err=True)
        return len(_warnings) == 0


config = Config()

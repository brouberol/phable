import os
import sys
from dataclasses import dataclass, field
from functools import partial


def os_getenv_or_raise(env_var_name: str):
    if val := os.getenv(env_var_name):
        return val
    sys.stderr.write(f"{env_var_name} is not set and is required\n")
    sys.stderr.flush()
    sys.exit(1)


def field_with_default_from_env(env_var_name):
    return field(default_factory=partial(os_getenv_or_raise, env_var_name))


@dataclass(frozen=True)
class Config:
    phabricator_url: str = field_with_default_from_env("PHABRICATOR_URL")
    phabricator_token: str = field_with_default_from_env("PHABRICATOR_TOKEN")
    phabricator_default_project_phid: str = field_with_default_from_env(
        "PHABRICATOR_DEFAULT_PROJECT_PHID"
    )


config = Config()

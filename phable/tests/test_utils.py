from pathlib import Path
from unittest import mock

import pytest

from phable.utils import text_from_cli_arg_or_fs_or_editor


def test_text_from_cli_arg_or_fs_or_editor_with_noting():
    with pytest.raises(ValueError):
        text_from_cli_arg_or_fs_or_editor()


def test_text_from_cli_arg_or_fs_or_editor_with_text_body():
    assert text_from_cli_arg_or_fs_or_editor(body="some text") == "some text"


def test_from_cli_arg_or_fs_or_editor_with_path(tmpdir):
    tmpfile: Path = tmpdir / "description.txt"
    tmpfile.write_text("some text", encoding="utf-8")
    assert text_from_cli_arg_or_fs_or_editor(path=tmpfile) == "some text"


def test_from_cli_arg_or_fs_or_editor_with_path_and_force_editor(tmpdir, monkeypatch):
    monkeypatch.setenv("EDITOR", "vim")
    tmpfile: Path = tmpdir / "description.txt"
    tmpfile.write_text("some text", encoding="utf-8")
    with mock.patch("phable.utils.subprocess.run") as m_sub_run:
        assert (
            text_from_cli_arg_or_fs_or_editor(path=tmpfile, force_editor=True)
            == "some text"
        )
        m_sub_run.assert_called_once_with(["vim", str(tmpfile)])

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import cast


def text_from_cli_arg_or_fs_or_editor(
    body: str | None = None, path: Path | None = None, force_editor: bool = False
) -> str:
    """Return argument text/file content, or return prompted input text.

    If some argument text is passed, and it matches a file path, return the file content.
    If it does not match a file path, return the text itself.
    Finally, if no argument is passed, open an editor and return the text written by the
    user.

    """
    if not (body or path):
        txt_tmpfile = tempfile.NamedTemporaryFile(
            encoding="utf-8", mode="w", suffix=".md"
        )
        subprocess.run([os.environ["EDITOR"], txt_tmpfile.name])
        return Path(txt_tmpfile.name).read_text(encoding="utf-8")

    if body:
        return body

    path = cast(Path, path)
    if not path.exists():
        raise ValueError(f"{path} does not exist")

    if not force_editor:
        return path.read_text(encoding="utf-8")

    editor = find_editor()

    subprocess.run([editor, path])
    return path.read_text(encoding="utf-8")


def find_editor() -> str:
    """
    Try and find a suitable editor for editing text.

    This tries the following things:

    - $EDITOR
    - sensible-editor (a Debianism)
    - nano

    If none of these work, emit a useful error message and exit with a
    non-zero status.
    """
    editor = os.environ.get("EDITOR")
    if editor:
        return editor

    editor = shutil.which("sensible-editor")
    if editor:
        return editor

    editor = shutil.which("nano")
    if editor:
        return editor

    # None of the choices worked out, emit a message and exit
    sys.stderr.write(
        "Could not find a suitable editor: $EDITOR is not set, and neither"
        " sensible-editor nor nano are in the path.\n"
    )
    sys.exit(1)

    # We never reach this
    return "/bin/false"

import os
import subprocess
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

    subprocess.run([os.environ["EDITOR"], path])
    return path.read_text(encoding="utf-8")

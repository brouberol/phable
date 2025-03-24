import tempfile
import subprocess
import os
from pathlib import Path


def text_from_cli_arg_or_fs_or_editor(body_or_path: str) -> str:
    """Return argument text/file content, or return prompted input text.

    If some argument text is passed, and it matches a file path, return the file content.
    If it does not match a file path, return the text itself.
    Finally, if no argument is passed, open an editor and return the text written by the
    user.

    """
    try:
        if body_or_path is not None and (local_file := Path(body_or_path)).exists():
            return local_file.read_text()
    except OSError:
        pass

    if not body_or_path:
        txt_tmpfile = tempfile.NamedTemporaryFile(
            encoding="utf-8", mode="w", suffix=".md"
        )
        subprocess.run([os.environ["EDITOR"], txt_tmpfile.name])
        return Path(txt_tmpfile.name).read_text()
    return body_or_path

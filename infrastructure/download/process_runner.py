import subprocess
from typing import Optional


class ProcessRunner:
    @staticmethod
    def popen(
        command: list[str],
        stdout=None,
        stderr=None,
        text: bool = True,
        encoding: Optional[str] = "utf-8",
        errors: str = "replace",
    ) -> subprocess.Popen:
        return subprocess.Popen(
            command,
            stdout=stdout,
            stderr=stderr,
            text=text,
            encoding=encoding,
            errors=errors,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
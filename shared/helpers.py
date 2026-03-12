import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication


def restart_application(
    quit_app: bool = True,
    login: Optional[str] = None,
    password: Optional[str] = None,
    **kwargs,
) -> None:
    args = ["--restart"]

    if login is not None:
        args.extend(["-login", login])
    if password is not None:
        args.extend(["-password", password])

    for key, value in kwargs.items():
        arg_key = f"-{key}" if len(key) == 1 else f"--{key}"
        if value is True:
            args.append(arg_key)
        elif isinstance(value, str):
            args.extend([arg_key, value])

    if getattr(sys, "frozen", False):
        executable = sys.executable
        restart_args = args
    else:
        executable = sys.executable
        filtered_args = []
        skip_next = False

        for arg in sys.argv:
            if skip_next:
                skip_next = False
                continue

            if arg in ["-login", "-password", "--restart"]:
                skip_next = True
                continue

            filtered_args.append(arg)

        restart_args = filtered_args + args

    subprocess.Popen([executable] + restart_args)

    if quit_app:
        QApplication.quit()


def extract_pubfileid(url_or_text: str) -> str:
    match = re.search(r"\b\d{8,10}\b", url_or_text)
    return match.group(0) if match else ""


def parse_file_size_to_bytes(size_str: str) -> int:
    if not size_str or not isinstance(size_str, str):
        return 0

    normalized = size_str.strip().upper().replace(",", ".")
    multipliers = {
        "TB": 1024 ** 4,
        "GB": 1024 ** 3,
        "MB": 1024 ** 2,
        "KB": 1024,
        "B": 1,
    }

    for suffix, multiplier in multipliers.items():
        if normalized.endswith(suffix):
            number_part = normalized[:-len(suffix)].strip()
            try:
                return int(float(number_part) * multiplier)
            except (ValueError, TypeError):
                return 0

    try:
        return int(float(normalized))
    except (ValueError, TypeError):
        return 0


def parse_depot_status(status_text: str) -> dict:
    result = {
        "downloaded_bytes": 0,
        "total_bytes": 0,
        "percent": -1.0,
    }

    if not status_text:
        return result

    progress_match = re.search(
        r"([\d.,]+)\s*(TB|GB|MB|KB|B)\s*/\s*([\d.,]+)\s*(TB|GB|MB|KB|B)",
        status_text,
        re.IGNORECASE,
    )
    if progress_match:
        downloaded = f"{progress_match.group(1)} {progress_match.group(2)}"
        total = f"{progress_match.group(3)} {progress_match.group(4)}"
        result["downloaded_bytes"] = parse_file_size_to_bytes(downloaded)
        result["total_bytes"] = parse_file_size_to_bytes(total)

    percent_match = re.search(r"([\d.,]+)\s*%", status_text)
    if percent_match:
        try:
            result["percent"] = float(percent_match.group(1).replace(",", "."))
        except ValueError:
            pass

    return result


def project_root() -> Path:
    return Path(__file__).resolve().parent.parent
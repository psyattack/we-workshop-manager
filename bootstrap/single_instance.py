import sys
import time
from tendo import singleton


def ensure_single_instance(argv: list[str]) -> None:
    is_restart = "--restart" in argv
    if is_restart:
        argv.remove("--restart")
        time.sleep(1)

    try:
        singleton.SingleInstance()
    except Exception:
        if not is_restart:
            sys.exit(0)
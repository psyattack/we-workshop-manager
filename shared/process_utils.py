import subprocess


def kill_process_by_name(process_name: str) -> bool:
    try:
        subprocess.run(
            f"taskkill /f /im {process_name}",
            creationflags=subprocess.CREATE_NO_WINDOW,
            check=False,
        )
        return True
    except Exception:
        return False
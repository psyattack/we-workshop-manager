import random
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable, Optional

import psutil
from PyQt6.QtCore import QObject, pyqtSignal

from domain.models.download import TaskStatus
from infrastructure.download.process_runner import ProcessRunner
from services.account_service import AccountService
from shared.constants import STEAM_APP_ID


class DownloadService(QObject):
    download_completed = pyqtSignal(str, bool)
    extraction_completed = pyqtSignal(str, bool)

    def __init__(self, we_directory: str, account_service: AccountService):
        super().__init__()
        self.we_directory = Path(we_directory)
        self.account_service = account_service

        self.downloading: dict[str, TaskStatus] = {}
        self.extracting: dict[str, TaskStatus] = {}

    def start_download(
        self,
        pubfileid: str,
        account_index: int,
        on_complete: Optional[Callable[[str, bool], None]] = None,
    ) -> bool:
        if pubfileid in self.downloading:
            return False

        username, password = self.account_service.get_credentials(account_index)
        output_dir = self.we_directory / "projects" / "myprojects" / pubfileid

        command = [
            "plugins/DepotDownloader/DepotDownloader.exe",
            "-app",
            STEAM_APP_ID,
            "-pubfile",
            pubfileid,
            "-verify-all",
            "-username",
            username,
            "-password",
            password,
            "-loginid",
            str(random.getrandbits(32)),
            "-max-downloads",
            "32",
            "-dir",
            str(output_dir),
        ]

        self.downloading[pubfileid] = TaskStatus(
            task_id=pubfileid,
            status="Starting...",
            account=username,
        )

        def run() -> None:
            try:
                process = ProcessRunner.popen(
                    command=command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )

                self.downloading[pubfileid].pid = process.pid

                if process.stdout:
                    for line in process.stdout:
                        if pubfileid not in self.downloading:
                            break

                        cleaned = line.strip()
                        if not cleaned:
                            continue

                        cleaned = cleaned.replace(str(output_dir) + "\\", ": ")
                        self.downloading[pubfileid].status = cleaned

                    process.stdout.close()

                process.wait()
                success = process.returncode == 0
                self.download_completed.emit(pubfileid, success)

                if on_complete:
                    on_complete(pubfileid, success)

            except Exception as error:
                if pubfileid in self.downloading:
                    self.downloading[pubfileid].status = f"Error: {error}"
                self.download_completed.emit(pubfileid, False)

            finally:
                self.downloading.pop(pubfileid, None)

        threading.Thread(target=run, daemon=True).start()
        return True

    def cancel_download(self, pubfileid: str) -> bool:
        info = self.downloading.get(pubfileid)
        if not info:
            return False

        if info.pid:
            try:
                process = psutil.Process(info.pid)
                process.terminate()
                process.wait(timeout=3)
            except Exception:
                pass

        folder_path = self.we_directory / "projects" / "myprojects" / pubfileid
        if folder_path.exists():
            shutil.rmtree(folder_path, ignore_errors=True)

        self.downloading.pop(pubfileid, None)
        return True

    def start_extraction(
        self,
        pubfileid: str,
        output_dir: Path,
        on_complete: Optional[Callable[[str, bool], None]] = None,
    ) -> bool:
        source_folder = self.we_directory / "projects" / "myprojects" / pubfileid
        if not source_folder.exists():
            return False

        if pubfileid in self.extracting:
            return False

        pkg_file = None
        for file in source_folder.iterdir():
            if file.is_file() and file.suffix.lower() == ".pkg":
                pkg_file = file
                break

        if not pkg_file:
            return False

        repkg_exe = Path("plugins/RePKG/RePKG.exe")
        if not repkg_exe.exists():
            return False

        extract_folder = output_dir / pubfileid
        command = [
            str(repkg_exe),
            "extract",
            "-c",
            "-n",
            "-o",
            str(extract_folder),
            str(pkg_file),
        ]

        self.extracting[pubfileid] = TaskStatus(
            task_id=pubfileid,
            status="Starting...",
            output_folder=str(extract_folder),
        )

        def run() -> None:
            try:
                process = ProcessRunner.popen(
                    command=command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )

                self.extracting[pubfileid].pid = process.pid

                if process.stdout:
                    for line in iter(process.stdout.readline, ""):
                        if pubfileid not in self.extracting:
                            break

                        cleaned = line.strip()
                        if not cleaned:
                            continue

                        self.extracting[pubfileid].status = cleaned[:100]

                process.wait()
                success = process.returncode == 0

                if pubfileid in self.extracting:
                    self.extracting[pubfileid].status = "Completed!" if success else "Failed"

                self.extraction_completed.emit(pubfileid, success)

                if on_complete:
                    on_complete(pubfileid, success)

                time.sleep(2)

            except Exception as error:
                if pubfileid in self.extracting:
                    self.extracting[pubfileid].status = f"Error: {str(error)[:80]}"
                self.extraction_completed.emit(pubfileid, False)

            finally:
                self.extracting.pop(pubfileid, None)

        threading.Thread(target=run, daemon=True).start()
        return True

    def is_downloading(self, pubfileid: str) -> bool:
        return pubfileid in self.downloading

    def is_extracting(self, pubfileid: str) -> bool:
        return pubfileid in self.extracting

    def get_download_status(self, pubfileid: str) -> str:
        task = self.downloading.get(pubfileid)
        return task.status if task else ""

    def get_extraction_status(self, pubfileid: str) -> str:
        task = self.extracting.get(pubfileid)
        return task.status if task else ""

    def cleanup_all(self) -> None:
        for pubfileid in list(self.downloading.keys()):
            self.cancel_download(pubfileid)

        for pubfileid, info in list(self.extracting.items()):
            if info.pid:
                try:
                    process = psutil.Process(info.pid)
                    process.terminate()
                    process.wait(timeout=3)
                except Exception:
                    pass

            if info.output_folder and Path(info.output_folder).exists():
                try:
                    shutil.rmtree(info.output_folder, ignore_errors=True)
                except Exception:
                    pass

        self.downloading.clear()
        self.extracting.clear()
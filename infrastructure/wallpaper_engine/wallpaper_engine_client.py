import json
import os
import subprocess
from pathlib import Path
from typing import Any, Optional

import psutil

from shared.constants import STEAM_APP_ID


class WallpaperEngineClient:
    def __init__(self, we_directory: str):
        self.we_directory = Path(we_directory)
        self.config_path = self.we_directory / "config.json"
        self.projects_path = self.we_directory / "projects" / "myprojects"

    @staticmethod
    def detect_installation() -> Optional[str]:
        seen: set[str] = set()
        candidate_paths: list[Path] = []

        for path in [
            Path("C:/Program Files (x86)/Wallpaper Engine"),
            Path("C:/Program Files/Wallpaper Engine"),
            Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Wallpaper Engine",
            Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Wallpaper Engine",
        ]:
            try:
                resolved = str(path.resolve())
            except Exception:
                resolved = str(path)

            if resolved not in seen:
                seen.add(resolved)
                candidate_paths.append(path)

        for candidate in candidate_paths:
            if not candidate.exists():
                continue

            if (candidate / "wallpaper64.exe").exists() or (candidate / "wallpaper32.exe").exists():
                return str(candidate)

        try:
            for process in psutil.process_iter(["name", "exe"]):
                name = process.info.get("name")
                exe = process.info.get("exe")
                if not name or not exe:
                    continue

                if name.lower() in ("wallpaper64.exe", "wallpaper32.exe"):
                    we_path = Path(exe).parent
                    if (we_path / "projects").exists():
                        return str(we_path)
        except Exception:
            return None

        return None

    def _get_executable(self) -> Optional[Path]:
        executable = self.we_directory / "wallpaper64.exe"
        if executable.exists():
            return executable

        executable = self.we_directory / "wallpaper32.exe"
        if executable.exists():
            return executable

        return None

    def _run_command(self, args: list[str]) -> bool:
        try:
            subprocess.Popen(
                args,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return True
        except Exception:
            return False

    def get_current_wallpaper_from_config(self, monitor: int = 0) -> Optional[str]:
        if not self.config_path.exists():
            return None

        try:
            with self.config_path.open("r", encoding="utf-8") as file:
                config = json.load(file)

            selected = (
                config.get("Main", {})
                .get("general", {})
                .get("wallpaperconfig", {})
                .get("selectedwallpapers", {})
            )
            return selected.get(f"Monitor{monitor}", {}).get("file")
        except Exception:
            return None

    def get_current_wallpaper_folder(self, monitor: int = 0) -> Optional[Path]:
        current = self.get_current_wallpaper_from_config(monitor)
        if not current:
            return None

        try:
            return Path(current).parent.resolve()
        except Exception:
            return None

    def get_current_wallpaper_pubfileid(self, monitor: int = 0) -> Optional[str]:
        folder = self.get_current_wallpaper_folder(monitor)
        if not folder:
            return None
        return folder.name

    def is_wallpaper_current(self, project_path: Path, monitor: int = 0) -> bool:
        current_folder = self.get_current_wallpaper_folder(monitor)
        if not current_folder:
            return False

        try:
            target = project_path.parent.resolve() if project_path.is_file() else project_path.resolve()
            return current_folder == target
        except Exception:
            return False

    def is_wallpaper_current_by_pubfileid(self, pubfileid: str, monitor: int = 0) -> bool:
        return self.get_current_wallpaper_pubfileid(monitor) == pubfileid

    def is_installed(self, pubfileid: str) -> bool:
        return (self.projects_path / pubfileid).exists()

    def get_installed_wallpapers(self) -> list[Path]:
        if not self.projects_path.exists():
            return []

        return [
            folder
            for folder in self.projects_path.iterdir()
            if folder.is_dir()
        ]

    def apply_wallpaper(self, project_json_path: Path, monitor: Optional[int] = None, force: bool = False) -> bool:
        executable = self._get_executable()
        if not executable:
            return False

        if project_json_path.is_dir():
            folder_path = project_json_path
            json_path = project_json_path / "project.json"
        else:
            folder_path = project_json_path.parent
            json_path = project_json_path

        if not force:
            pubfileid = folder_path.name
            if self.is_wallpaper_current_by_pubfileid(pubfileid, monitor or 0):
                return True

        args = [
            str(executable),
            "-control",
            "openWallpaper",
            "-file",
            str(json_path.resolve()),
        ]
        if monitor is not None:
            args.extend(["-monitor", str(monitor)])

        return self._run_command(args)

    def apply_profile(self, profile_name: str) -> bool:
        executable = self._get_executable()
        if not executable:
            return False

        return self._run_command(
            [
                str(executable),
                "-control",
                "openProfile",
                "-profile",
                profile_name,
            ]
        )

    def apply_properties(self, properties: dict[str, Any], monitor: Optional[int] = None) -> bool:
        if not properties:
            return False

        executable = self._get_executable()
        if not executable:
            return False

        try:
            processed: dict[str, Any] = {}
            for key, value in properties.items():
                if isinstance(value, bool):
                    processed[key] = value
                elif isinstance(value, float) and value == int(value):
                    processed[key] = int(value)
                elif isinstance(value, (int, float)):
                    processed[key] = value
                else:
                    processed[key] = str(value)

            properties_json = json.dumps(processed, ensure_ascii=False, separators=(",", ":"))
            raw_properties = f"RAW~({properties_json})~END"

            args = [
                str(executable),
                "-control",
                "applyProperties",
                "-properties",
                raw_properties,
            ]
            if monitor is not None:
                args.extend(["-monitor", str(monitor)])

            return self._run_command(args)
        except Exception:
            return False

    def apply_single_property(self, key: str, value: Any, monitor: Optional[int] = None) -> bool:
        return self.apply_properties({key: value}, monitor)

    def open_wallpaper_engine(self, show_window: bool = True) -> bool:
        executable = self._get_executable()
        if not executable:
            return False

        try:
            is_running = False
            for process in psutil.process_iter(["name"]):
                name = process.info.get("name")
                if name and name.lower() == executable.name.lower():
                    is_running = True
                    break

            if is_running and show_window:
                return self._run_command([str(executable), "-showwindow"])

            if not is_running:
                return self._run_command([str(executable)])

            return True
        except Exception:
            return False
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
import psutil

class WallpaperEngine:
    def __init__(self, we_directory: str):
        self.we_directory = Path(we_directory)
        self.config_path = self.we_directory / "config.json"
        self.projects_path = self.we_directory / "projects" / "myprojects"

    @staticmethod
    def detect_installation() -> Optional[str]:
        seen = set()
        common_paths = []
        for p in [
            Path("C:/Program Files (x86)/Wallpaper Engine"),
            Path("C:/Program Files/Wallpaper Engine"),
            Path(os.environ.get("ProgramFiles", "C:/Program Files") + "/Wallpaper Engine"),
            Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)") + "/Wallpaper Engine"),
        ]:
            resolved = str(p.resolve())
            if resolved not in seen:
                seen.add(resolved)
                common_paths.append(p)

        for we_path in common_paths:
            if we_path.exists():
                if (we_path / "wallpaper64.exe").exists() or (we_path / "wallpaper32.exe").exists():
                    return str(we_path)

        try:
            for proc in psutil.process_iter(['name', 'exe']):
                name = proc.info['name']
                exe = proc.info['exe']
                if name and exe and name.lower() in ("wallpaper64.exe", "wallpaper32.exe"):
                    we_path = Path(exe).parent
                    if (we_path / "projects").exists():
                        return str(we_path)
        except Exception as e:
            print(f"Process scan error: {e}")

        return None

    def _get_executable(self) -> Optional[Path]:
        we_exe = self.we_directory / "wallpaper64.exe"
        if not we_exe.exists():
            we_exe = self.we_directory / "wallpaper32.exe"
        return we_exe if we_exe.exists() else None

    def _run_command(self, cmd: str) -> bool:
        try:
            os.system(f'start /b "" {cmd}')
            return True
        except Exception as e:
            print(f"[WallpaperEngine] Command error: {e}")
            return False

    def get_current_wallpaper_from_config(self, monitor: int = 0) -> Optional[str]:
        if not self.config_path.exists():
            print(f"[WallpaperEngine] Config not found: {self.config_path}")
            return None
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            selected = (
                config.get("Main", {})
                .get("general", {})
                .get("wallpaperconfig", {})
                .get("selectedwallpapers", {})
            )
            file_path = selected.get(f"Monitor{monitor}", {}).get("file")
            return file_path
        except Exception as e:
            print(f"[WallpaperEngine] Error reading config: {e}")
            return None

    def get_current_wallpaper_folder(self, monitor: int = 0) -> Optional[Path]:
        current = self.get_current_wallpaper_from_config(monitor)
        if not current:
            return None
        try:
            folder = Path(current).parent.resolve()
            return folder
        except Exception as e:
            print(f"[WallpaperEngine] Error getting folder: {e}")
            return None

    def get_current_wallpaper_pubfileid(self, monitor: int = 0) -> Optional[str]:
        folder = self.get_current_wallpaper_folder(monitor)
        if folder:
            pubfileid = folder.name
            return pubfileid
        return None

    def is_wallpaper_current(self, project_path: Path, monitor: int = 0) -> bool:
        current_folder = self.get_current_wallpaper_folder(monitor)
        if not current_folder:
            return False
        try:
            target_folder = project_path.parent.resolve() if project_path.is_file() else project_path.resolve()
            result = current_folder == target_folder
            return result
        except Exception as e:
            print(f"[WallpaperEngine] Error comparing: {e}")
            return False

    def is_wallpaper_current_by_pubfileid(self, pubfileid: str, monitor: int = 0) -> bool:
        current_pubfileid = self.get_current_wallpaper_pubfileid(monitor)
        result = current_pubfileid == pubfileid
        return result

    def is_installed(self, pubfileid: str) -> bool:
        return (self.projects_path / pubfileid).exists()

    def get_installed_wallpapers(self) -> list:
        if not self.projects_path.exists():
            return []
        return [folder for folder in self.projects_path.iterdir() if folder.is_dir()]

    def apply_wallpaper(self, project_json_path: Path, monitor: Optional[int] = None, force: bool = False) -> bool:
        we_exe = self._get_executable()
        if not we_exe:
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

        cmd = f'"{we_exe}" -control openWallpaper -file "{json_path.resolve()}"'
        if monitor is not None:
            cmd += f' -monitor {monitor}'
        return self._run_command(cmd)

    def apply_profile(self, profile_name: str) -> bool:
        we_exe = self._get_executable()
        if not we_exe:
            return False
        return self._run_command(f'"{we_exe}" -control openProfile -profile "{profile_name}"')

    def apply_properties(self, properties: Dict[str, Any], monitor: Optional[int] = None) -> bool:
        if not properties:
            return False
        we_exe = self._get_executable()
        if not we_exe:
            return False
        try:
            processed_props = {}
            for key, value in properties.items():
                if isinstance(value, bool):
                    processed_props[key] = value
                elif isinstance(value, float) and value == int(value):
                    processed_props[key] = int(value)
                elif isinstance(value, (int, float)):
                    processed_props[key] = value
                else:
                    processed_props[key] = str(value)

            properties_json = json.dumps(processed_props, ensure_ascii=False, separators=(',', ':'))
            raw_properties = f'RAW~({properties_json})~END'
            cmd = f'"{we_exe}" -control applyProperties -properties {raw_properties}'
            if monitor is not None:
                cmd += f' -monitor {monitor}'
            return self._run_command(cmd)
        except Exception as e:
            print(f"[WallpaperEngine] Error: {e}")
            return False

    def apply_single_property(self, key: str, value: Any, monitor: Optional[int] = None) -> bool:
        return self.apply_properties({key: value}, monitor)

    def open_wallpaper_engine(self, show_window: bool = True) -> bool:
        try:
            we_exe = self._get_executable()
            if not we_exe:
                return False

            is_running = False
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and proc.info['name'].lower() == we_exe.name.lower():
                    is_running = True
                    break

            if is_running and show_window:
                return self._run_command(f'"{we_exe}" -showwindow')
            elif not is_running:
                return self._run_command(f'"{we_exe}"')
            return True
        except Exception as e:
            print(f"Error opening WE: {e}")
            return False

import json
import subprocess
from pathlib import Path
from typing import Optional
import psutil
import os

class WallpaperEngine:
    def __init__(self, we_directory: str):
        self.we_directory = Path(we_directory)
        self.config_path = self.we_directory / "config.json"
        self.projects_path = self.we_directory / "projects" / "myprojects"
    
    @staticmethod
    def detect_installation() -> Optional[str]:
        common_paths = [
            Path("C:/Program Files (x86)/Wallpaper Engine"),
            Path("C:/Program Files/Wallpaper Engine"),
            Path(os.environ.get("ProgramFiles", "C:/Program Files") + "/Wallpaper Engine"),
            Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)") + "/Wallpaper Engine")
        ]
        
        for we_path in common_paths:
            if we_path.exists():
                if (we_path / "wallpaper64.exe").exists() or (we_path / "wallpaper32.exe").exists():
                    return str(we_path)
        
        try:
            for proc in psutil.process_iter(['name', 'exe']):
                name = proc.info['name']
                exe = proc.info['exe']
                if name and exe:
                    if name.lower() in ("wallpaper64.exe", "wallpaper32.exe"):
                        we_path = Path(exe).parent
                        if (we_path / "projects").exists():
                            return str(we_path)
        except Exception as e:
            print(f"Process scan error: {e}")
        
        return None
    
    def is_wallpaper_active(self, project_path: Path) -> bool:
        if not self.config_path.exists():
            return False
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            selected_wallpapers = config.get("Main", {}).get("general", {}).get(
                "wallpaperconfig", {}
            ).get("selectedwallpapers", {})
            
            monitor0_info = selected_wallpapers.get("Monitor0", {})
            active_file = monitor0_info.get("file")
            
            if not active_file:
                return False
            
            active_folder = Path(active_file).parent.resolve()
            project_folder = project_path.resolve()
            
            return active_folder == project_folder
            
        except Exception as e:
            print(f"Error checking active wallpaper: {e}")
            return False
    
    def apply_wallpaper(self, project_json_path: Path) -> bool:
        try:
            we_exe = self.we_directory / "wallpaper64.exe"
            if not we_exe.exists():
                we_exe = self.we_directory / "wallpaper32.exe"
            
            if not we_exe.exists():
                return False
            
            cmd = [
                str(we_exe),
                "-control", "openWallpaper",
                "-file", str(project_json_path.resolve())
            ]
            
            subprocess.Popen(
                cmd,
                cwd=str(self.we_directory),
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            return True
            
        except Exception as e:
            print(f"Error applying wallpaper: {e}")
            return False
    
    def open_wallpaper_engine(self, show_window: bool = True) -> bool:
        try:
            we_exe = self.we_directory / "wallpaper64.exe"
            if not we_exe.exists():
                we_exe = self.we_directory / "wallpaper32.exe"
            
            if not we_exe.exists():
                return False
            
            is_running = False
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and proc.info['name'].lower() == we_exe.name.lower():
                    is_running = True
                    break
            
            if is_running and show_window:
                subprocess.Popen(
                    [str(we_exe), "-showwindow"],
                    cwd=str(self.we_directory),
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            elif not is_running:
                subprocess.Popen(
                    [str(we_exe)],
                    cwd=str(self.we_directory),
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            
            return True
            
        except Exception as e:
            print(f"Error opening WE: {e}")
            return False
    
    def is_installed(self, pubfileid: str) -> bool:
        project_path = self.projects_path / pubfileid
        return project_path.exists()
    
    def get_installed_wallpapers(self) -> list:
        if not self.projects_path.exists():
            return []
        
        return [
            folder for folder in self.projects_path.iterdir()
            if folder.is_dir()
        ]
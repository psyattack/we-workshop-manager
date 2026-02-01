import os
import time
from pathlib import Path
from typing import Union
import shutil
import re
import subprocess

def human_readable_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def get_directory_size(path: Union[str, Path]) -> int:
    total = 0
    path = Path(path)
    
    try:
        for root, dirs, files in os.walk(path):
            for file in files:
                try:
                    file_path = Path(root) / file
                    total += file_path.stat().st_size
                except Exception:
                    pass
    except Exception:
        pass
    
    return total

def get_folder_mtime(path: Union[str, Path]) -> float:
    try:
        return Path(path).stat().st_mtime
    except Exception:
        return 0.0

def format_timestamp(timestamp: float, fmt: str = "%Y-%m-%d %H:%M") -> str:
    try:
        return time.strftime(fmt, time.localtime(timestamp))
    except Exception:
        return "Unknown"

def ensure_directory(path: Union[str, Path]) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def clear_cache_if_needed(cache_path: Union[str, Path], max_size_mb: int = 200) -> bool:
    cache_path = Path(cache_path)
    
    if not cache_path.exists():
        return False
    
    try:
        total_size = get_directory_size(cache_path)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if total_size >= max_size_bytes:
            shutil.rmtree(cache_path)
            return True
    except Exception as e:
        print(f"Error clearing cache: {e}")
    
    return False

def extract_pubfileid(url_or_text: str) -> str:
    match = re.search(r'\b\d{8,10}\b', url_or_text)
    return match.group(0) if match else ""

def kill_process_by_name(process_name: str) -> bool:
    try:
        subprocess.run(
            f"taskkill /f /im {process_name}",
            creationflags=subprocess.CREATE_NO_WINDOW,
            check=False
        )
        return True
    except Exception:
        return False

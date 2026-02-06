import random
import subprocess
import threading
from pathlib import Path
from typing import Dict, Callable, Optional
from PyQt6.QtCore import QObject, pyqtSignal
import psutil
import shutil
import time

class DownloadManager(QObject):
    download_completed = pyqtSignal(str, bool)  # pubfileid, success
    extraction_completed = pyqtSignal(str, bool)  # pubfileid, success
    
    def __init__(self, we_directory: str, account_manager):
        super().__init__()
        self.we_directory = Path(we_directory)
        self.account_manager = account_manager
        
        self.downloading: Dict[str, dict] = {}
        self.extracting: Dict[str, dict] = {}
    
    def start_download(
        self,
        pubfileid: str,
        account_index: int,
        on_complete: Optional[Callable] = None
    ) -> bool:

        if pubfileid in self.downloading:
            return False
        
        account, password = self.account_manager.get_credentials(account_index)
        output_dir = self.we_directory / "projects" / "myprojects" / pubfileid
        
        command = [
            "Plugins/DepotDownloaderMod/DepotDownloaderMod.exe",
            "-app", "431960",
            "-pubfile", pubfileid,
            "-verify-all",
            "-username", account,
            "-password", password,
            "-loginid", str(random.getrandbits(32)),
            "-max-downloads", "32",
            "-dir", str(output_dir)
        ]
        
        def run_download():
            try:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                self.downloading[pubfileid] = {
                    "pid": process.pid,
                    "status": "Starting...",
                    "account": account
                }
                
                for line in process.stdout:
                    if line.strip() and pubfileid in self.downloading:
                        clean_line = line.strip().replace(str(output_dir) + "\\", ": ")
                        self.downloading[pubfileid]["status"] = clean_line
                
                process.stdout.close()
                process.wait()
                
                success = process.returncode == 0
                self.download_completed.emit(pubfileid, success)
                
                if on_complete:
                    on_complete(pubfileid, success)
                
            except Exception as e:
                print(f"Download error for {pubfileid}: {e}")
                if pubfileid in self.downloading:
                    self.downloading[pubfileid]["status"] = f"Error: {str(e)}"
                self.download_completed.emit(pubfileid, False)
            finally:
                self.downloading.pop(pubfileid, None)
        
        self.downloading[pubfileid] = {"status": "Starting..."}
        threading.Thread(target=run_download, daemon=True).start()
        return True
    
    def cancel_download(self, pubfileid: str) -> bool:
        info = self.downloading.get(pubfileid)
        if not info:
            return False
        
        pid = info.get("pid")
        if pid:
            try:
                proc = psutil.Process(pid)
                proc.terminate()
                proc.wait(timeout=3)
            except:
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
        on_complete: Optional[Callable] = None
    ) -> bool:
        source_folder = self.we_directory / "projects" / "myprojects" / pubfileid
        
        if not source_folder.exists():
            return False
        
        pkg_file = None
        for file in source_folder.iterdir():
            if file.is_file() and file.suffix.lower() == '.pkg':
                pkg_file = file
                break
        
        if not pkg_file:
            return False
        
        repkg_exe = Path("Plugins/RePKG/RePKG.exe")
        if not repkg_exe.exists():
            return False
        
        if pubfileid in self.extracting:
            return False
        
        extract_folder = output_dir / pubfileid
        
        command = [
            str(repkg_exe),
            "extract",
            "-c", "-n",
            "-o", str(extract_folder),
            str(pkg_file)
        ]
        
        def run_extraction():
            try:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                self.extracting[pubfileid] = {
                    "pid": process.pid,
                    "status": "Starting...",
                    "output_folder": str(extract_folder)
                }
                
                for line in iter(process.stdout.readline, ''):
                    if line.strip() and pubfileid in self.extracting:
                        clean_line = line.strip()[:100]
                        self.extracting[pubfileid]["status"] = clean_line
                
                process.wait()
                success = process.returncode == 0
                
                if pubfileid in self.extracting:
                    self.extracting[pubfileid]["status"] = "✅ Completed!" if success else "❌ Failed"
                
                self.extraction_completed.emit(pubfileid, success)
                
                if on_complete:
                    on_complete(pubfileid, success)
                
                time.sleep(2)
                
            except Exception as e:
                print(f"Extraction error for {pubfileid}: {e}")
                if pubfileid in self.extracting:
                    self.extracting[pubfileid]["status"] = f"❌ Error: {str(e)[:80]}"
                self.extraction_completed.emit(pubfileid, False)
            finally:
                self.extracting.pop(pubfileid, None)
        
        threading.Thread(target=run_extraction, daemon=True).start()
        return True
    
    def is_downloading(self, pubfileid: str) -> bool:
        return pubfileid in self.downloading
    
    def is_extracting(self, pubfileid: str) -> bool:
        return pubfileid in self.extracting
    
    def get_download_status(self, pubfileid: str) -> str:
        info = self.downloading.get(pubfileid)
        if info:
            return info.get("status", "Unknown")
        return ""
    
    def get_extraction_status(self, pubfileid: str) -> str:
        info = self.extracting.get(pubfileid)
        if info:
            return info.get("status", "Unknown")
        return ""
    
    def cleanup_all(self):
        for pubfileid in list(self.downloading.keys()):
            self.cancel_download(pubfileid)
        
        for pubfileid, info in list(self.extracting.items()):
            pid = info.get("pid")
            if pid:
                try:
                    proc = psutil.Process(pid)
                    proc.terminate()
                    proc.wait(timeout=3)
                except:
                    pass
            
            output_folder = info.get("output_folder")
            if output_folder and Path(output_folder).exists():
                try:
                    shutil.rmtree(output_folder, ignore_errors=True)
                except:
                    pass
        
        self.downloading.clear()
        self.extracting.clear()

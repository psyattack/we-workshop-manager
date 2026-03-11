"""
Entry point
"""

# ----------------------------------
import sys
import time
from tendo import singleton

_is_restart = "--restart" in sys.argv
if _is_restart:
    sys.argv.remove("--restart")
    time.sleep(1)

try:
    me = singleton.SingleInstance()
except:
    if not _is_restart:
        sys.exit()
# ----------------------------------

from pathlib import Path
from PyQt6.QtWidgets import QApplication, QFileDialog
from ui.notifications import MessageBox
from core.config_manager import ConfigManager
from core.accounts import AccountManager
from core.download_manager import DownloadManager
from core.wallpaper_engine import WallpaperEngine
from core.theme_manager import ThemeManager
from localization.translator import Translator
from ui.main_window import MainWindow
from resources.icons import get_icon

def setup_wallpaper_engine(config: ConfigManager, translator) -> str:
    we_directory = config.get_directory()

    if not we_directory:
        we_directory = WallpaperEngine.detect_installation()

    if we_directory and Path(we_directory, "projects", "myprojects").exists():
        config.set_directory(we_directory)
        return we_directory

    while True:
        directory = QFileDialog.getExistingDirectory(
            None,
            translator.t("messages.select_we_folder"),
            str(Path.home())
        )
        
        if not directory:
            sys.exit(0)
        
        if Path(directory, "projects", "myprojects").exists():
            config.set_directory(directory)
            return directory
        
        MessageBox.warning(
            None,
            translator.t("dialog.warning"),
            translator.t("messages.invalid_we_directory")
        )

def main():
    app = QApplication(sys.argv)
    
    config = ConfigManager()
    accounts = AccountManager()
    translator = Translator(config.get_language())
    theme_manager = ThemeManager()
    
    we_directory = setup_wallpaper_engine(config, translator)
    
    # Inits
    wallpaper_engine = WallpaperEngine(we_directory)
    download_manager = DownloadManager(we_directory, accounts)
    
    # Theme
    theme_manager.set_theme(config.get_theme(), app)
    
    # Main window
    window = MainWindow(
        config,
        accounts,
        download_manager,
        wallpaper_engine,
        translator,
        theme_manager
    )
    window.setWindowIcon(get_icon("ICON_APP"))
    
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

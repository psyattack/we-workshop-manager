"""
Entry point
"""

# ----------------------------------
import sys
from tendo import singleton

try:
    me = singleton.SingleInstance()
except:
    sys.exit()
# ----------------------------------

import subprocess
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox, QFileDialog

from core.config_manager import ConfigManager
from core.accounts import AccountManager
from core.download_manager import DownloadManager
from core.wallpaper_engine import WallpaperEngine

from ui.themes.theme_manager import ThemeManager
from localization.translator import Translator
from ui.main_window import MainWindow

def check_dotnet_runtime() -> bool:
    try:
        result = subprocess.run(
            ["dotnet", "--list-runtimes"],
            capture_output=True,
            text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return "Microsoft.WindowsDesktop.App 9" in result.stdout
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def install_dotnet_runtime(translator) -> bool:
    packages_dir = Path("Packages")
    installer_path = None
    
    if packages_dir.exists():
        installers = list(packages_dir.glob("windowsdesktop-runtime-9.*-win-x64.exe"))
        if installers:
            installer_path = installers[0]
    
    if not installer_path or not installer_path.exists():
        QMessageBox.warning(
            None,
            translator.t("dialog.warning"),
            translator.t("messages.dotnet_installation_failed")
        )
        return False
    
    try:
        subprocess.Popen(
            [str(installer_path)],
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP
        )
        return True
    except Exception as e:
        QMessageBox.critical(
            None,
            translator.t("dialog.error"),
            f"Failed to start installer: {str(e)}"
        )
        return False

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
        
        QMessageBox.warning(
            None,
            translator.t("dialog.warning"),
            "Invalid Wallpaper Engine directory.\nPlease select the correct folder."
        )

def main():
    app = QApplication(sys.argv)
    
    config = ConfigManager()
    accounts = AccountManager()
    translator = Translator(config.get_language())
    theme_manager = ThemeManager()
    
    # .NET Runtime
    if not check_dotnet_runtime():
        msg_box = QMessageBox()
        msg_box.setWindowTitle(".NET 9 Desktop Runtime Required")
        msg_box.setText(translator.t("messages.dotnet_required"))
        msg_box.setInformativeText(translator.t("messages.dotnet_install_now"))
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        
        response = msg_box.exec()
        
        if response == QMessageBox.StandardButton.Yes:
            if install_dotnet_runtime(translator):
                QMessageBox.information(
                    None,
                    "Installation Started",
                    translator.t("messages.dotnet_installation_started")
                )
            else:
                QMessageBox.warning(
                    None,
                    translator.t("dialog.warning"),
                    translator.t("messages.dotnet_warning")
                )
                sys.exit(0)
        else:
            QMessageBox.information(
                None,
                translator.t("dialog.warning"),
                translator.t("messages.dotnet_warning")
            )
            sys.exit(0)

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
    
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

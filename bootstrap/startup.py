from pathlib import Path

from PyQt6.QtWidgets import QFileDialog

from bootstrap.context import ApplicationContext
from ui.notifications import MessageBox

from services.config_service import ConfigService
from services.account_service import AccountService
from services.translation_service import TranslationService
from services.theme_service import ThemeService
from services.metadata_service import MetadataService

from infrastructure.wallpaper_engine.wallpaper_engine_client import WallpaperEngineClient
from infrastructure.download.download_service import DownloadService
from infrastructure.resources.resource_manager import get_icon

from ui.main_window import MainWindow


def _setup_wallpaper_engine_directory(
    config_service: ConfigService,
    translation_service: TranslationService,
) -> str:
    we_directory = config_service.get_directory()
    if we_directory:
        projects_path = Path(we_directory) / "projects" / "myprojects"
        if projects_path.exists():
            return we_directory

    detected = WallpaperEngineClient.detect_installation()
    if detected:
        projects_path = Path(detected) / "projects" / "myprojects"
        if projects_path.exists():
            config_service.set_directory(detected)
            return detected

    while True:
        directory = QFileDialog.getExistingDirectory(
            None,
            translation_service.t("messages.select_we_folder"),
            str(Path.home()),
        )
        if not directory:
            raise SystemExit(0)

        if (Path(directory) / "projects" / "myprojects").exists():
            config_service.set_directory(directory)
            return directory

        MessageBox.warning(
            None,
            translation_service.t("dialog.warning"),
            translation_service.t("messages.invalid_we_directory"),
        )


def create_application_context(app) -> ApplicationContext:
    config_service = ConfigService()
    translation_service = TranslationService(config_service.get_language())
    account_service = AccountService.from_runtime_arguments()
    theme_service = ThemeService()

    we_directory = _setup_wallpaper_engine_directory(
        config_service=config_service,
        translation_service=translation_service,
    )

    wallpaper_engine_client = WallpaperEngineClient(we_directory)
    metadata_service = MetadataService(config_service)
    download_service = DownloadService(
        we_directory=we_directory,
        account_service=account_service,
    )

    theme_service.apply_theme(config_service.get_theme(), app)

    main_window = MainWindow(
        config_service=config_service,
        account_service=account_service,
        download_service=download_service,
        wallpaper_engine_client=wallpaper_engine_client,
        translation_service=translation_service,
        theme_service=theme_service,
        metadata_service=metadata_service,
    )
    main_window.setWindowIcon(get_icon("ICON_APP"))

    return ApplicationContext(
        app=app,
        config_service=config_service,
        account_service=account_service,
        translation_service=translation_service,
        theme_service=theme_service,
        wallpaper_engine_client=wallpaper_engine_client,
        download_service=download_service,
        main_window=main_window,
    )
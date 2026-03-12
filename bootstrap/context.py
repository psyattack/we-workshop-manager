from dataclasses import dataclass
from typing import Any


@dataclass
class ApplicationContext:
    app: Any
    config_service: Any
    account_service: Any
    translation_service: Any
    theme_service: Any
    wallpaper_engine_client: Any
    download_service: Any
    main_window: Any
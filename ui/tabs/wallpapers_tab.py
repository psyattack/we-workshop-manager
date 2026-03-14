import json
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QTimer, Qt, pyqtProperty
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from shared.filesystem import get_directory_size, get_folder_mtime
from shared.formatting import human_readable_size
from ui.widgets.details_panel import DetailsPanel
from ui.widgets.filter_bar import UnifiedFilterBar, LocalFilters
from ui.widgets.flow_layout import AdaptiveGridWidget
from ui.widgets.grid_items import LocalGridItem


class AnimatedDetailsContainerLocal(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._target_width = 320
        self._current_width = 320
        self._is_panel_visible = True

        self._animation = QPropertyAnimation(self, b"panelWidth")
        self._animation.setDuration(250)
        self._animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._animation.finished.connect(self._on_animation_finished)

        self.setFixedWidth(self._target_width)
        self.setMinimumWidth(0)

    def get_panel_width(self) -> int:
        return self._current_width

    def set_panel_width(self, width: int) -> None:
        self._current_width = width
        self.setFixedWidth(max(0, width))

    panelWidth = pyqtProperty(int, get_panel_width, set_panel_width)

    def set_target_width(self, width: int) -> None:
        self._target_width = width
        if self._is_panel_visible:
            self._current_width = width
            self.setFixedWidth(width)

    def is_panel_visible(self) -> bool:
        return self._is_panel_visible

    def show_panel(self) -> None:
        if self._is_panel_visible:
            return
        self._is_panel_visible = True
        self.setVisible(True)
        for child in self.findChildren(QWidget):
            child.setVisible(True)
        self._animation.stop()
        self._animation.setStartValue(0)
        self._animation.setEndValue(self._target_width)
        self._animation.start()

    def hide_panel(self) -> None:
        if not self._is_panel_visible:
            return
        self._is_panel_visible = False
        self._animation.stop()
        self._animation.setStartValue(self._current_width)
        self._animation.setEndValue(0)
        self._animation.start()

    def _on_animation_finished(self) -> None:
        if not self._is_panel_visible:
            self.setVisible(False)


class WallpapersTab(QWidget):
    def __init__(
        self,
        config_service,
        download_service,
        wallpaper_engine_client,
        translator,
        theme_manager,
        metadata_service=None,
        parent=None,
    ):
        super().__init__(parent)
        self.config = config_service
        self.dm = download_service
        self.we = wallpaper_engine_client
        self.tr = translator
        self.theme = theme_manager
        self.metadata_service = metadata_service

        self.selected_folder = None
        self.grid_items: list[LocalGridItem] = []
        self._is_refreshing = False
        self._all_wallpapers_data: list[dict[str, Any]] = []
        self._details_panel_margin = 15

        self._setup_ui()

        self.dm.download_completed.connect(self._on_download_completed)
        self.load_wallpapers()

    def _setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        self.left_panel = self._create_left_panel()
        main_layout.addWidget(self.left_panel, 1)

        self.details_container = AnimatedDetailsContainerLocal(self)
        self.details_container.set_target_width(312)

        details_outer_layout = QVBoxLayout(self.details_container)
        details_outer_layout.setContentsMargins(0, 0, 0, 0)
        details_outer_layout.setSpacing(0)

        self.details_card = QFrame()
        self.details_card.setObjectName("wallpapersDetailsCard")
        self.details_card.setStyleSheet(
            f"""
            QFrame#wallpapersDetailsCard {{
                background-color: {self.theme.get_color('bg_secondary')};
                border: 1px solid {self.theme.get_color('border')};
                border-radius: 16px;
            }}
            """
        )

        details_layout = QVBoxLayout(self.details_card)
        details_layout.setContentsMargins(0, 0, 0, 0)

        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.details_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.details_panel = DetailsPanel(
            self.we,
            self.dm,
            self.tr,
            self.theme,
            self.config,
            self.metadata_service,
            self,
        )
        self.details_panel.panel_collapse_requested.connect(self._on_collapse_requested)

        self.details_scroll.setWidget(self.details_panel)
        details_layout.addWidget(self.details_scroll)
        details_outer_layout.addWidget(self.details_card)

        main_layout.addWidget(self.details_container)

    def _create_left_panel(self) -> QWidget:
        widget = QWidget()
        outer_layout = QVBoxLayout(widget)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.content_card = QFrame()
        self.content_card.setObjectName("wallpapersContentCard")
        self.content_card.setStyleSheet(
            f"""
            QFrame#wallpapersContentCard {{
                background-color: {self.theme.get_color('bg_secondary')};
                border: 1px solid {self.theme.get_color('border')};
                border-radius: 16px;
            }}
            """
        )

        layout = QVBoxLayout(self.content_card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.filter_bar = UnifiedFilterBar(self.theme, self.tr, UnifiedFilterBar.MODE_LOCAL, self)
        self.filter_bar.filters_changed.connect(self._on_filters_changed)
        self.filter_bar.refresh_requested.connect(self._on_refresh_requested)
        layout.addWidget(self.filter_bar, 0, Qt.AlignmentFlag.AlignHCenter)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(
            f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {self.theme.get_color('bg_secondary')};
                width: 10px;
                margin: 2px 2px 2px 2px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {self.theme.get_color('border')};
                min-height: 30px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {self.theme.get_color('primary')};
            }}
            QScrollBar::handle:vertical:pressed {{
                background-color: {self.theme.get_color('primary_hover')};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            """
        )

        self.grid_widget = AdaptiveGridWidget()
        self.grid_widget.set_item_size_range(160, 240, 185)
        self.grid_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.scroll_area.setWidget(self.grid_widget)
        layout.addWidget(self.scroll_area)

        outer_layout.addWidget(self.content_card)
        return widget

    def _on_collapse_requested(self) -> None:
        self.details_container.hide_panel()
        self._update_grid_margin(False)

    def _update_grid_margin(self, panel_visible: bool) -> None:
        if panel_visible:
            self.content_card.layout().setContentsMargins(10, 10, 10, 10)
        else:
            self.content_card.layout().setContentsMargins(10, 10, 10, 10)

    def _on_filters_changed(self, filters: LocalFilters) -> None:
        self._apply_filters_and_display(filters)

    def _on_refresh_requested(self) -> None:
        self.load_wallpapers()

    def _on_download_completed(self, pubfileid: str, success: bool) -> None:
        if success and not self._is_refreshing:
            QTimer.singleShot(800, self._safe_refresh)

    def _safe_refresh(self) -> None:
        if self._is_refreshing:
            return
        try:
            self._is_refreshing = True
            self.refresh()
        finally:
            QTimer.singleShot(500, self._reset_refresh_flag)

    def _reset_refresh_flag(self) -> None:
        self._is_refreshing = False

    def _load_wallpaper_data(self, wallpaper_path: Path) -> dict[str, Any]:
        pubfileid = wallpaper_path.name
        data = {
            "path": wallpaper_path,
            "pubfileid": pubfileid,
            "title": pubfileid,
            "install_date": get_folder_mtime(wallpaper_path),
            "size": get_directory_size(wallpaper_path),
            "tags": {},
            "rating": 0,
            "posted_date": 0,
            "updated_date": 0,
        }

        project_json = wallpaper_path / "project.json"
        if project_json.exists():
            try:
                with project_json.open("r", encoding="utf-8") as file:
                    project_data = json.load(file)
                data["title"] = project_data.get("title", pubfileid)
            except Exception:
                pass

        metadata = self.metadata_service.get(pubfileid) if self.metadata_service else None
        if metadata:
            data["tags"] = metadata.tags
            data["rating"] = metadata.rating
            data["posted_date"] = metadata.posted_date
            data["updated_date"] = metadata.updated_date

        return data

    def _extract_tags_from_metadata(self, tags_dict: dict) -> dict[str, list[str] | str]:
        result = {
            "category": "",
            "type": "",
            "age_rating": "",
            "resolution": "",
            "misc": [],
            "genre": [],
        }
        if not tags_dict:
            return result

        result["category"] = tags_dict.get("Category", "")
        result["type"] = tags_dict.get("Type", "")
        result["age_rating"] = tags_dict.get("Age Rating", "")
        result["resolution"] = tags_dict.get("Resolution", "")

        misc_value = tags_dict.get("Miscellaneous", "")
        if misc_value:
            result["misc"] = [tag.strip() for tag in misc_value.split(",") if tag.strip()]

        genre_value = tags_dict.get("Genre", "")
        if genre_value:
            result["genre"] = [tag.strip() for tag in genre_value.split(",") if tag.strip()]

        return result

    def _matches_filters(self, wallpaper_data: dict[str, Any], filters: LocalFilters) -> bool:
        if filters.search:
            search_lower = filters.search.lower()
            title = wallpaper_data.get("title", "").lower()
            pubfileid = wallpaper_data.get("pubfileid", "").lower()
            if search_lower not in title and search_lower not in pubfileid:
                return False

        tags = self._extract_tags_from_metadata(wallpaper_data.get("tags", {}))

        if filters.category and tags["category"] != filters.category:
            return False
        if filters.type_tag and tags["type"] != filters.type_tag:
            return False
        if filters.age_rating and tags["age_rating"] != filters.age_rating:
            return False
        if filters.resolution and tags["resolution"] != filters.resolution:
            return False

        for required_tag in filters.misc_tags:
            if required_tag not in tags["misc"]:
                return False
        for excluded_tag in filters.excluded_misc_tags:
            if excluded_tag in tags["misc"]:
                return False

        for required_tag in filters.genre_tags:
            if required_tag not in tags["genre"]:
                return False
        for excluded_tag in filters.excluded_genre_tags:
            if excluded_tag in tags["genre"]:
                return False

        return True

    def _sort_wallpapers(self, wallpapers: list[dict[str, Any]], filters: LocalFilters) -> list[dict[str, Any]]:
        reverse = filters.sort_order == "desc"

        if filters.sort == "name":
            return sorted(wallpapers, key=lambda item: item.get("title", "").lower(), reverse=reverse)
        if filters.sort == "rating":
            return sorted(wallpapers, key=lambda item: item.get("rating", 0), reverse=reverse)
        if filters.sort == "size":
            return sorted(wallpapers, key=lambda item: item.get("size", 0), reverse=reverse)
        if filters.sort == "posted_date":
            return sorted(wallpapers, key=lambda item: item.get("posted_date", 0), reverse=reverse)
        if filters.sort == "updated_date":
            return sorted(wallpapers, key=lambda item: item.get("updated_date", 0), reverse=reverse)

        return sorted(wallpapers, key=lambda item: item.get("install_date", 0), reverse=reverse)

    def _apply_filters_and_display(self, filters: LocalFilters) -> None:
        filtered = [item for item in self._all_wallpapers_data if self._matches_filters(item, filters)]
        sorted_wallpapers = self._sort_wallpapers(filtered, filters)
        self._display_wallpapers(sorted_wallpapers)

    def load_wallpapers(self) -> None:
        self._clear_grid()

        wallpaper_paths = [
            wallpaper
            for wallpaper in self.we.get_installed_wallpapers()
            if wallpaper.name not in self.dm.downloading and wallpaper.exists()
        ]

        self._all_wallpapers_data = [self._load_wallpaper_data(path) for path in wallpaper_paths]

        filters = self.filter_bar.get_current_filters()
        filtered = [item for item in self._all_wallpapers_data if self._matches_filters(item, filters)]
        sorted_wallpapers = self._sort_wallpapers(filtered, filters)

        self._display_wallpapers(sorted_wallpapers)

        total_size = get_directory_size(self.we.projects_path)
        self._update_info_text(len(sorted_wallpapers), len(self._all_wallpapers_data), total_size)

        QTimer.singleShot(50, self._force_grid_update)

        if sorted_wallpapers and not self.selected_folder:
            self._on_item_clicked(str(sorted_wallpapers[0]["path"]))

    def _force_grid_update(self) -> None:
        self.grid_widget.update_layout()
        self.grid_widget.updateGeometry()
        self.scroll_area.updateGeometry()

    def _show_empty_state(self, text: str) -> None:
        container = QWidget()
        container.setMinimumHeight(120)
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        container.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        label = QLabel(text)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 16px;
            padding: 10px;
            background: transparent;
            """
        )
        layout.addWidget(label)

        self.grid_widget.add_item(container)

    def _display_wallpapers(self, wallpapers: list[dict[str, Any]]) -> None:
        self._clear_grid()

        if not wallpapers:
            self._update_info_text(0, len(self._all_wallpapers_data), get_directory_size(self.we.projects_path))
            self._show_empty_state(self.tr.t("labels.no_wallpapers_found"))
            return

        item_size = self.grid_widget.get_current_item_size()
        for wallpaper_data in wallpapers:
            item = LocalGridItem(str(wallpaper_data["path"]), item_size, self.theme, self)
            item.clicked.connect(self._on_item_clicked)
            self.grid_widget.add_item(item)
            self.grid_items.append(item)

        total_size = get_directory_size(self.we.projects_path)
        self._update_info_text(len(wallpapers), len(self._all_wallpapers_data), total_size)

        QTimer.singleShot(50, self._force_grid_update)

    def _clear_grid(self) -> None:
        for item in self.grid_items:
            if hasattr(item, "release_resources"):
                try:
                    item.release_resources()
                except RuntimeError:
                    pass

        self.grid_widget.clear_items()
        self.grid_items.clear()

    def _update_info_text(self, filtered_count: int, total_count: int, total_size: int) -> None:
        primary = self.tr.t("labels.wallpapers_filtered", filtered=filtered_count, total=total_count)
        secondary = self.tr.t("labels.total_size", size=human_readable_size(total_size))
        self.filter_bar.set_info_texts(primary=primary, secondary=secondary)

    def _on_item_clicked(self, folder_path: str) -> None:
        if not self.details_container.is_panel_visible():
            self.details_container.show_panel()
            self._update_grid_margin(True)

        if not Path(folder_path).exists():
            return

        self.selected_folder = folder_path
        self.details_panel.set_installed_folder(folder_path)

    def refresh(self) -> None:
        selected = self.selected_folder
        self.load_wallpapers()

        if selected and Path(selected).exists():
            self._on_item_clicked(selected)
        else:
            self.selected_folder = None

    def release_resources_for_folder(self, folder_path: str) -> None:
        if hasattr(self, "details_panel") and self.details_panel.folder_path == folder_path:
            self.details_panel.release_resources()

        for item in self.grid_items:
            if hasattr(item, "folder_path") and item.folder_path == folder_path:
                if hasattr(item, "release_resources"):
                    try:
                        item.release_resources()
                    except RuntimeError:
                        pass

        if self.selected_folder == folder_path:
            self.selected_folder = None
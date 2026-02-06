from pathlib import Path

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QScrollArea, QGridLayout, QSplitter,
    QSizePolicy, QFrame, QGraphicsDropShadowEffect
)

from ui.grid_items import LocalGridItem
from ui.details_panel import DetailsPanel
from utils.helpers import get_directory_size, human_readable_size, get_folder_mtime

class WallpapersTab(QWidget):

    def __init__(self, config_manager, download_manager, wallpaper_engine, translator, theme_manager, parent=None):
        super().__init__(parent)

        self.config = config_manager
        self.dm = download_manager
        self.we = wallpaper_engine
        self.tr = translator
        self.theme = theme_manager

        self.sort_mode = "date"
        self.selected_folder = None
        self.items = []
        self._is_refreshing = False

        self._setup_ui()

        self.dm.download_completed.connect(self._on_download_completed)

        self.load_wallpapers()

    def _setup_ui(self):
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        left_widget = self._create_left_panel()

        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setFixedWidth(320)
        self.details_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.details_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.details_panel = DetailsPanel(
            self.we, self.dm, self.tr, self.theme, self.config, self
        )
        self.details_scroll.setWidget(self.details_panel)

        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(self.details_scroll)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.splitter)

        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self._recalculate_grid)
        self.splitter.splitterMoved.connect(lambda: self.resize_timer.start(100))

    def _create_left_panel(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(20, 20, 5, 10)
        layout.setSpacing(20)

        layout.addWidget(self._create_header())

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)

        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setHorizontalSpacing(2)
        self.grid_layout.setVerticalSpacing(2)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        self.grid_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.scroll_area.setWidget(self.grid_widget)

        layout.addWidget(self.scroll_area)
        return widget

    def _create_header(self) -> QFrame:
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.theme.get_color('primary_hover')},
                    stop:1 {self.theme.get_color('primary_pressed')});
                border-radius: 16px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(91, 141, 239, 100))
        shadow.setOffset(0, 5)
        header.setGraphicsEffect(shadow)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(20)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.count_label = QLabel()
        self.count_label.setStyleSheet("""
            font-weight: 800;
            font-size: 24px;
            color: white;
            background: transparent;
        """)

        self.size_label = QLabel()
        self.size_label.setStyleSheet("""
            font-weight: 600;
            font-size: 13px;
            color: rgba(255, 255, 255, 0.9);
            background: transparent;
        """)

        info_layout.addWidget(self.count_label)
        info_layout.addWidget(self.size_label)
        layout.addLayout(info_layout)
        layout.addStretch()

        sort_container = QWidget()
        sort_container.setFixedWidth(160)
        sort_container.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 10px;
            }
        """)

        sort_layout = QVBoxLayout(sort_container)
        sort_layout.setContentsMargins(12, 8, 12, 8)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems([
            self.tr.t("labels.sort_date"),
            self.tr.t("labels.sort_name")
        ])
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        self.sort_combo.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.sort_combo.setStyleSheet("""
            QComboBox {
                background: transparent;
                color: white;
                border: none;
                font-weight: 600;
                font-size: 13px;
                padding: 4px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid white;
            }
            QComboBox QAbstractItemView {
                background-color: rgba(26, 29, 46, 0.95);
                color: white;
                selection-background-color: rgba(91, 141, 239, 0.5);
                border: 2px solid rgba(91, 141, 239, 0.3);
                border-radius: 8px;
            }
        """)

        sort_layout.addWidget(self.sort_combo)
        layout.addWidget(sort_container)

        return header

    def _on_sort_changed(self, index):
        self.sort_mode = "date" if index == 0 else "name"
        self.load_wallpapers()

    def _on_download_completed(self, pubfileid: str, success: bool):
        if success and not self._is_refreshing:
            QTimer.singleShot(800, self._safe_refresh)

    def _safe_refresh(self):
        if self._is_refreshing:
            return
        try:
            self._is_refreshing = True
            self.refresh()
        finally:
            QTimer.singleShot(500, self._reset_refresh_flag)

    def _reset_refresh_flag(self):
        self._is_refreshing = False

    def load_wallpapers(self, columns=None):
        self._clear_grid()

        wallpapers = [
            w for w in self.we.get_installed_wallpapers()
            if w.name not in self.dm.downloading and w.exists()
        ]

        if not wallpapers:
            self._update_info(0, 0)
            return

        if self.sort_mode == "date":
            wallpapers.sort(key=lambda w: get_folder_mtime(w), reverse=True)
        else:
            wallpapers.sort(key=lambda w: w.name.lower())

        if columns is None:
            columns = self._calculate_columns()

        item_size = self._calculate_item_size(columns)

        row = col = 0
        for wallpaper_path in wallpapers:
            item = LocalGridItem(str(wallpaper_path), item_size, self)
            item.clicked.connect(self._on_item_clicked)
            self.grid_layout.addWidget(item, row, col)
            self.items.append(item)
            col += 1
            if col >= columns:
                col = 0
                row += 1

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.grid_layout.addWidget(spacer, row + 1, 0, 1, max(1, columns))
        self.items.append(spacer)

        total_size = get_directory_size(self.we.projects_path)
        self._update_info(len(wallpapers), total_size)

        if wallpapers and not self.selected_folder:
            self._on_item_clicked(str(wallpapers[0]))

    def _calculate_columns(self) -> int:
        available_width = self.scroll_area.viewport().width()
        if available_width <= 0:
            return 4
        TARGET_SIZE = 190
        return min(max(1, available_width // (TARGET_SIZE + 2)), 8)

    def _calculate_item_size(self, columns: int) -> int:
        if columns <= 0:
            return 185
        available_width = self.scroll_area.viewport().width()
        if available_width <= 0:
            return 185

        total_spacing = (columns - 1) * 2
        ideal_size = (available_width - total_spacing) // columns
        item_size = max(160, min(ideal_size, 240))

        if available_width > 1000:
            item_size = min(item_size, 230)
        elif available_width > 800:
            item_size = min(item_size, 210)
        elif available_width > 600:
            item_size = min(item_size, 190)
        else:
            item_size = max(160, item_size)

        return item_size

    def _clear_grid(self):
        for item in self.items:
            if hasattr(item, 'release_resources'):
                try:
                    item.release_resources()
                except RuntimeError:
                    pass

        while self.grid_layout.count():
            layout_item = self.grid_layout.takeAt(0)
            if layout_item and layout_item.widget():
                widget = layout_item.widget()
                widget.setParent(None)
                widget.deleteLater()

        self.items.clear()

    def _update_info(self, count: int, total_size: int):
        self.count_label.setText(self.tr.t("labels.wallpapers_count", count=count))
        self.size_label.setText(self.tr.t("labels.total_size", size=human_readable_size(total_size)))

    def _on_item_clicked(self, folder_path: str):
        if not Path(folder_path).exists():
            return
        self.selected_folder = folder_path
        self.details_panel.set_installed_folder(folder_path)

    def refresh(self):
        selected = self.selected_folder
        self.load_wallpapers()
        if selected and Path(selected).exists():
            self._on_item_clicked(selected)
        else:
            self.selected_folder = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'resize_timer'):
            self.resize_timer.start(100)

    def _recalculate_grid(self):
        selected = self.selected_folder
        self.load_wallpapers(columns=self._calculate_columns())
        if selected and Path(selected).exists():
            self._on_item_clicked(selected)

    def release_resources_for_folder(self, folder_path: str):
        if hasattr(self, 'details_panel') and self.details_panel.folder_path == folder_path:
            self.details_panel.release_resources()

        for item in self.items:
            if hasattr(item, 'folder_path') and item.folder_path == folder_path:
                if hasattr(item, 'release_resources'):
                    try:
                        item.release_resources()
                    except RuntimeError:
                        pass

        if self.selected_folder == folder_path:
            self.selected_folder = None

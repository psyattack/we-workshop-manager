from dataclasses import dataclass, field

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from domain.config.workshop_filter_config import WorkshopFilterConfig
from domain.models.workshop import WorkshopFilters
from infrastructure.resources.resource_manager import get_icon, get_pixmap
from ui.widgets.filter_tag_widgets import FilterTagsFlowWidget
from ui.widgets.popup_panel import PopupPanel
from ui.widgets.search_panel import SearchPanel


@dataclass
class LocalFilters:
    search: str = ""
    sort: str = "install_date"
    sort_order: str = "desc"
    category: str = ""
    type_tag: str = ""
    age_rating: str = ""
    resolution: str = ""
    misc_tags: list[str] = field(default_factory=list)
    genre_tags: list[str] = field(default_factory=list)
    excluded_misc_tags: list[str] = field(default_factory=list)
    excluded_genre_tags: list[str] = field(default_factory=list)


class LocalFilterConfig:
    SORT_KEYS = ["install_date", "name", "rating", "size", "posted_date", "updated_date"]

    @classmethod
    def get_translated_sort_options(cls, translator):
        translations = {
            "install_date": translator("filters.local_sort.install_date"),
            "name": translator("filters.local_sort.name"),
            "rating": translator("filters.local_sort.rating"),
            "size": translator("filters.local_sort.size"),
            "posted_date": translator("filters.local_sort.posted_date"),
            "updated_date": translator("filters.local_sort.updated_date"),
        }
        fallback = {
            "install_date": "Install Date",
            "name": "Name",
            "rating": "Rating",
            "size": "Size",
            "posted_date": "Posted Date",
            "updated_date": "Updated Date",
        }
        for key in cls.SORT_KEYS:
            if translations[key] == f"filters.local_sort.{key}":
                translations[key] = fallback[key]
        return translations


class UnifiedActionsPanel(PopupPanel):
    clear_requested = pyqtSignal()
    refresh_requested = pyqtSignal()

    def __init__(self, theme_manager, translator, parent=None):
        super().__init__(theme_manager, title=translator.t("labels.action"), parent=parent)
        self.tr = translator
        self._setup_ui()
        self.hide()

    def _setup_ui(self) -> None:
        self.setFixedWidth(210)

        layout = self.body_layout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        title = QLabel(self.tr.t("labels.action"))
        title.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_primary')};
            background: transparent;
            font-size: 15px;
            font-weight: 700;
            padding: 0 0 2px 0;
            """
        )
        layout.addWidget(title)

        self.clear_button = self._create_action_button(
            text=self.tr.t("labels.clear").strip(),
            icon_name="ICON_CLOSE2",
            callback=self._on_clear,
        )
        self.refresh_button = self._create_action_button(
            text=self.tr.t("tooltips.refresh"),
            icon_name="ICON_REFRASH",
            callback=self._on_refresh,
        )

        layout.addWidget(self.clear_button)
        layout.addWidget(self.refresh_button)

    def _create_action_button(self, text: str, icon_name: str, callback) -> QPushButton:
        button = QPushButton()
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedHeight(34)
        button.clicked.connect(callback)
        button.setText("")

        row = QHBoxLayout(button)
        row.setContentsMargins(10, 0, 12, 0)
        row.setSpacing(8)

        icon_label = QLabel()
        pixmap = get_pixmap(icon_name, size=20)
        if pixmap.isNull():
            icon = get_icon(icon_name)
            pixmap = icon.pixmap(20, 20)
        icon_label.setPixmap(pixmap)
        icon_label.setFixedSize(20, 20)
        icon_label.setStyleSheet("background: transparent; border: none;")

        text_label = QLabel(text)
        text_label.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_primary')};
            background: transparent;
            font-size: 12px;
            font-weight: 600;
            """
        )

        row.addWidget(icon_label)
        row.addWidget(text_label)
        row.addStretch()

        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 8px;
                text-align: left;
                padding: 0;
            }}
            QPushButton:hover {{
                background-color: {self.theme.get_color('bg_elevated')};
            }}
            """
        )
        return button

    def _on_clear(self) -> None:
        self.clear_requested.emit()
        self.hide_and_emit()

    def _on_refresh(self) -> None:
        self.refresh_requested.emit()
        self.hide_and_emit()


class WorkshopFiltersPanel(PopupPanel):
    filters_changed = pyqtSignal()

    def __init__(self, theme_manager, translator, parent=None):
        super().__init__(theme_manager, title=translator.t("labels.filters"), parent=parent)
        self.tr = translator
        self._setup_ui()
        self.hide()

    def _setup_ui(self) -> None:
        self.setFixedWidth(575)

        layout = self.body_layout()
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        title = QLabel(self.tr.t("labels.filters"))
        title.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_primary')};
            background: transparent;
            font-size: 15px;
            font-weight: 700;
            padding: 0 0 2px 0;
            """
        )
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        combo_w = 165

        self.sort_combo = self._create_combo(
            self.tr.t("labels.sort"),
            WorkshopFilterConfig.get_translated_sort_options(self.tr.t),
            combo_w,
        )
        self.time_combo = self._create_combo(
            self.tr.t("labels.period"),
            WorkshopFilterConfig.get_translated_time_periods(self.tr.t),
            combo_w,
        )
        self.time_combo["combo"].setCurrentIndex(1)

        self.category_combo = self._create_combo(
            self.tr.t("labels.category"),
            WorkshopFilterConfig.get_translated_categories(self.tr.t),
            combo_w,
        )
        self.type_combo = self._create_combo(
            self.tr.t("labels.type"),
            WorkshopFilterConfig.get_translated_types(self.tr.t),
            combo_w,
        )
        self.age_combo = self._create_combo(
            self.tr.t("labels.age"),
            WorkshopFilterConfig.get_translated_age_ratings(self.tr.t),
            combo_w,
        )
        self.resolution_combo = self._create_combo(
            self.tr.t("labels.resolution"),
            WorkshopFilterConfig.get_translated_resolutions(self.tr.t),
            combo_w,
        )
        self.asset_type_combo = self._create_combo(
            self.tr.t("labels.asset_type"),
            WorkshopFilterConfig.get_translated_asset_types(self.tr.t),
            combo_w,
        )
        self.asset_genre_combo = self._create_combo(
            self.tr.t("labels.asset_genre"),
            WorkshopFilterConfig.get_translated_asset_genres(self.tr.t),
            combo_w,
        )
        self.script_type_combo = self._create_combo(
            self.tr.t("labels.script_type"),
            WorkshopFilterConfig.get_translated_script_types(self.tr.t),
            combo_w,
        )

        combos = [
            self.sort_combo,
            self.time_combo,
            self.category_combo,
            self.type_combo,
            self.age_combo,
            self.resolution_combo,
            self.asset_type_combo,
            self.asset_genre_combo,
            self.script_type_combo,
        ]

        for index, combo_pack in enumerate(combos):
            row = index // 3
            col = index % 3
            grid.addWidget(combo_pack["container"], row, col)

        layout.addLayout(grid)

        for combo_pack in combos:
            combo_pack["combo"].currentIndexChanged.connect(self.filters_changed.emit)

        self.sort_combo["combo"].currentIndexChanged.connect(self._on_sort_changed)

        sections_row = QHBoxLayout()
        sections_row.setContentsMargins(0, 0, 0, 0)
        sections_row.setSpacing(12)
        sections_row.setAlignment(Qt.AlignmentFlag.AlignTop)

        misc_col = QWidget()
        misc_layout = QVBoxLayout(misc_col)
        misc_layout.setContentsMargins(0, 0, 0, 0)
        misc_layout.setSpacing(6)

        misc_title = self._section_label(self.tr.t("labels.miscellaneous"))
        misc_layout.addWidget(misc_title, alignment=Qt.AlignmentFlag.AlignLeft)

        misc_translations = WorkshopFilterConfig.get_translated_misc_tags(self.tr.t)
        self.misc_tags_widget = FilterTagsFlowWidget(
            tags=WorkshopFilterConfig.MISC_TAG_KEYS,
            translated_map=misc_translations,
            theme_manager=self.theme,
            max_width=255,
            parent=self,
        )
        self.misc_tags_widget.changed.connect(self.filters_changed.emit)
        misc_layout.addWidget(self.misc_tags_widget, alignment=Qt.AlignmentFlag.AlignTop)

        genre_col = QWidget()
        genre_layout = QVBoxLayout(genre_col)
        genre_layout.setContentsMargins(0, 0, 0, 0)
        genre_layout.setSpacing(6)

        genre_title = self._section_label(self.tr.t("labels.genre"))
        genre_layout.addWidget(genre_title, alignment=Qt.AlignmentFlag.AlignLeft)

        genre_translations = WorkshopFilterConfig.get_translated_genre_tags(self.tr.t)
        self.genre_tags_widget = FilterTagsFlowWidget(
            tags=WorkshopFilterConfig.GENRE_TAG_KEYS,
            translated_map=genre_translations,
            theme_manager=self.theme,
            max_width=255,
            parent=self,
        )
        self.genre_tags_widget.changed.connect(self.filters_changed.emit)
        genre_layout.addWidget(self.genre_tags_widget, alignment=Qt.AlignmentFlag.AlignTop)

        sections_row.addWidget(misc_col, 1, Qt.AlignmentFlag.AlignTop)
        sections_row.addWidget(genre_col, 1, Qt.AlignmentFlag.AlignTop)

        layout.addLayout(sections_row)

        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 2, 0, 0)
        bottom_row.setSpacing(10)

        self.incompatible_checkbox = QCheckBox(self.tr.t("labels.incompatible_items"))
        self.incompatible_checkbox.setStyleSheet(self._checkbox_style())
        self.incompatible_checkbox.stateChanged.connect(self.filters_changed.emit)

        bottom_row.addWidget(self.incompatible_checkbox)
        bottom_row.addStretch()

        layout.addLayout(bottom_row)

        self._on_sort_changed()

    def _create_combo(self, label_text: str, options: dict[str, str], width: int) -> dict:
        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        label = QLabel(label_text)
        label.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 10px;
            font-weight: 700;
            background: transparent;
            """
        )

        combo = QComboBox()
        combo.setFixedWidth(width)
        combo.setFixedHeight(28)
        combo.setStyleSheet(self._combo_style())

        for value, text in options.items():
            combo.addItem(text, value)

        layout.addWidget(label)
        layout.addWidget(combo)
        return {"container": container, "label": label, "combo": combo}

    def _combo_style(self) -> str:
        return f"""
        QComboBox {{
            background-color: {self.theme.get_color('bg_secondary')};
            color: {self.theme.get_color('text_primary')};
            border: 1px solid {self.theme.get_color('border')};
            border-radius: 6px;
            padding: 2px 8px;
            font-size: 11px;
            min-height: 22px;
        }}
        QComboBox:hover {{
            border-color: {self.theme.get_color('border_light')};
            background-color: {self.theme.get_color('bg_elevated')};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 18px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {self.theme.get_color('bg_elevated')};
            color: {self.theme.get_color('text_primary')};
            selection-background-color: {self.theme.get_color('primary')};
            border: none;
            border-radius: 8px;
        }}
        """

    def _checkbox_style(self) -> str:
        return f"""
        QCheckBox {{
            color: {self.theme.get_color('text_primary')};
            font-size: 11px;
            spacing: 6px;
        }}
        QCheckBox::indicator {{
            width: 13px;
            height: 13px;
            border-radius: 3px;
            border: 1px solid {self.theme.get_color('border')};
            background: {self.theme.get_color('bg_secondary')};
        }}
        QCheckBox::indicator:checked {{
            background: {self.theme.get_color('primary')};
            border-color: {self.theme.get_color('primary')};
        }}
        """

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 10px;
            font-weight: 700;
            background: transparent;
            margin: 0;
            padding: 0;
            """
        )
        return label

    def _on_sort_changed(self) -> None:
        is_trend = self.sort_combo["combo"].currentData() == "trend"
        self.time_combo["combo"].setEnabled(is_trend)

    def get_filters(self, search_text: str, page: int) -> WorkshopFilters:
        required_flags = []
        if self.incompatible_checkbox.isChecked():
            required_flags.append("incompatible")

        return WorkshopFilters(
            search=search_text.strip(),
            sort=self.sort_combo["combo"].currentData() or "trend",
            days=self.time_combo["combo"].currentData() or "7",
            category=self.category_combo["combo"].currentData() or "",
            type_tag=self.type_combo["combo"].currentData() or "",
            age_rating=self.age_combo["combo"].currentData() or "",
            resolution=self.resolution_combo["combo"].currentData() or "",
            misc_tags=self.misc_tags_widget.get_included(),
            genre_tags=self.genre_tags_widget.get_included(),
            excluded_misc_tags=self.misc_tags_widget.get_excluded(),
            excluded_genre_tags=self.genre_tags_widget.get_excluded(),
            asset_type=self.asset_type_combo["combo"].currentData() or "",
            asset_genre=self.asset_genre_combo["combo"].currentData() or "",
            script_type=self.script_type_combo["combo"].currentData() or "",
            required_flags=required_flags,
            page=page,
        )

    def clear_filters(self) -> None:
        self.sort_combo["combo"].setCurrentIndex(0)
        self.time_combo["combo"].setCurrentIndex(1)
        self.category_combo["combo"].setCurrentIndex(0)
        self.type_combo["combo"].setCurrentIndex(0)
        self.age_combo["combo"].setCurrentIndex(0)
        self.resolution_combo["combo"].setCurrentIndex(0)
        self.asset_type_combo["combo"].setCurrentIndex(0)
        self.asset_genre_combo["combo"].setCurrentIndex(0)
        self.script_type_combo["combo"].setCurrentIndex(0)
        self.incompatible_checkbox.setChecked(False)
        self.misc_tags_widget.reset_all()
        self.genre_tags_widget.reset_all()


class LocalFiltersPanel(PopupPanel):
    filters_changed = pyqtSignal()

    def __init__(self, theme_manager, translator, parent=None):
        super().__init__(theme_manager, title=translator.t("labels.filters"), parent=parent)
        self.tr = translator
        self._sort_order = "desc"
        self._setup_ui()
        self.hide()

    def _setup_ui(self) -> None:
        self.setFixedWidth(575)

        layout = self.body_layout()
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(10)

        title = QLabel(self.tr.t("labels.filters"))
        title.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_primary')};
            background: transparent;
            font-size: 15px;
            font-weight: 700;
            padding: 0 0 2px 0;
            """
        )
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)

        combo_w = 165

        self.sort_combo = self._create_combo(
            self.tr.t("labels.sort"),
            LocalFilterConfig.get_translated_sort_options(self.tr.t),
            combo_w,
        )
        self.category_combo = self._create_combo(
            self.tr.t("labels.category"),
            WorkshopFilterConfig.get_translated_categories(self.tr.t),
            combo_w,
        )
        self.type_combo = self._create_combo(
            self.tr.t("labels.type"),
            WorkshopFilterConfig.get_translated_types(self.tr.t),
            combo_w,
        )
        self.age_combo = self._create_combo(
            self.tr.t("labels.age"),
            WorkshopFilterConfig.get_translated_age_ratings(self.tr.t),
            combo_w,
        )
        self.resolution_combo = self._create_combo(
            self.tr.t("labels.resolution"),
            WorkshopFilterConfig.get_translated_resolutions(self.tr.t),
            combo_w,
        )

        combos = [
            self.sort_combo,
            self.category_combo,
            self.type_combo,
            self.age_combo,
            self.resolution_combo,
        ]

        for index, combo_pack in enumerate(combos):
            row = index // 3
            col = index % 3
            grid.addWidget(combo_pack["container"], row, col)

        layout.addLayout(grid)

        for combo_pack in combos:
            combo_pack["combo"].currentIndexChanged.connect(self.filters_changed.emit)

        sections_row = QHBoxLayout()
        sections_row.setContentsMargins(0, 0, 0, 0)
        sections_row.setSpacing(12)
        sections_row.setAlignment(Qt.AlignmentFlag.AlignTop)

        misc_col = QWidget()
        misc_layout = QVBoxLayout(misc_col)
        misc_layout.setContentsMargins(0, 0, 0, 0)
        misc_layout.setSpacing(6)

        misc_title = self._section_label(self.tr.t("labels.miscellaneous"))
        misc_layout.addWidget(misc_title, alignment=Qt.AlignmentFlag.AlignLeft)

        misc_translations = WorkshopFilterConfig.get_translated_misc_tags(self.tr.t)
        self.misc_tags_widget = FilterTagsFlowWidget(
            tags=WorkshopFilterConfig.MISC_TAG_KEYS,
            translated_map=misc_translations,
            theme_manager=self.theme,
            max_width=255,
            parent=self,
        )
        self.misc_tags_widget.changed.connect(self.filters_changed.emit)
        misc_layout.addWidget(self.misc_tags_widget, alignment=Qt.AlignmentFlag.AlignTop)

        genre_col = QWidget()
        genre_layout = QVBoxLayout(genre_col)
        genre_layout.setContentsMargins(0, 0, 0, 0)
        genre_layout.setSpacing(6)

        genre_title = self._section_label(self.tr.t("labels.genre"))
        genre_layout.addWidget(genre_title, alignment=Qt.AlignmentFlag.AlignLeft)

        genre_translations = WorkshopFilterConfig.get_translated_genre_tags(self.tr.t)
        self.genre_tags_widget = FilterTagsFlowWidget(
            tags=WorkshopFilterConfig.GENRE_TAG_KEYS,
            translated_map=genre_translations,
            theme_manager=self.theme,
            max_width=255,
            parent=self,
        )
        self.genre_tags_widget.changed.connect(self.filters_changed.emit)
        genre_layout.addWidget(self.genre_tags_widget, alignment=Qt.AlignmentFlag.AlignTop)

        sections_row.addWidget(misc_col, 1, Qt.AlignmentFlag.AlignTop)
        sections_row.addWidget(genre_col, 1, Qt.AlignmentFlag.AlignTop)

        layout.addLayout(sections_row)

        bottom_row = QHBoxLayout()
        bottom_row.setContentsMargins(0, 2, 0, 0)
        bottom_row.setSpacing(8)

        sort_order_label = QLabel(self.tr.t("tooltips.sort_order") + ":")
        sort_order_label.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 11px;
            font-weight: 700;
            background: transparent;
            """
        )

        self.sort_order_button = QPushButton("↓")
        self.sort_order_button.setCheckable(True)
        self.sort_order_button.setChecked(False)
        self.sort_order_button.setFixedSize(22, 22)
        self.sort_order_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sort_order_button.clicked.connect(self._toggle_sort_order)
        self.sort_order_button.setStyleSheet(self._toggle_style())

        bottom_row.addWidget(sort_order_label)
        bottom_row.addWidget(self.sort_order_button)
        bottom_row.addStretch()

        layout.addLayout(bottom_row)

    def _create_combo(self, label_text: str, options: dict[str, str], width: int) -> dict:
        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")

        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)

        label = QLabel(label_text)
        label.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 10px;
            font-weight: 700;
            background: transparent;
            """
        )

        combo = QComboBox()
        combo.setFixedWidth(width)
        combo.setFixedHeight(28)
        combo.setStyleSheet(self._combo_style())

        for value, text in options.items():
            combo.addItem(text, value)

        layout.addWidget(label)
        layout.addWidget(combo)

        return {"container": container, "label": label, "combo": combo}

    def _combo_style(self) -> str:
        return f"""
        QComboBox {{
            background-color: {self.theme.get_color('bg_secondary')};
            color: {self.theme.get_color('text_primary')};
            border: none;
            border-radius: 6px;
            padding: 2px 8px;
            font-size: 11px;
            min-height: 22px;
        }}
        QComboBox:hover {{
            background-color: {self.theme.get_color('bg_elevated')};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 18px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {self.theme.get_color('bg_elevated')};
            color: {self.theme.get_color('text_primary')};
            selection-background-color: {self.theme.get_color('primary')};
            border: none;
            border-radius: 8px;
        }}
        """

    def _toggle_style(self) -> str:
        return f"""
        QPushButton {{
            background-color: {self.theme.get_color('bg_secondary')};
            color: {self.theme.get_color('text_primary')};
            border: 1px solid {self.theme.get_color('border')};
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            padding: 0;
        }}
        QPushButton:hover {{
            background-color: {self.theme.get_color('bg_elevated')};
        }}
        QPushButton:checked {{
            background-color: {self.theme.get_color('primary')};
            color: white;
            border: 1px solid {self.theme.get_color('primary')};
        }}
        """

    def _section_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_secondary')};
            font-size: 10px;
            font-weight: 700;
            background: transparent;
            margin: 0;
            padding: 0;
            """
        )
        return label

    def _toggle_sort_order(self) -> None:
        self._sort_order = "asc" if self._sort_order == "desc" else "desc"
        self.sort_order_button.setChecked(self._sort_order == "asc")
        self.sort_order_button.setText("↑" if self._sort_order == "asc" else "↓")
        self.filters_changed.emit()

    def get_filters(self, search_text: str) -> LocalFilters:
        return LocalFilters(
            search=search_text.strip(),
            sort=self.sort_combo["combo"].currentData() or "install_date",
            sort_order=self._sort_order,
            category=self.category_combo["combo"].currentData() or "",
            type_tag=self.type_combo["combo"].currentData() or "",
            age_rating=self.age_combo["combo"].currentData() or "",
            resolution=self.resolution_combo["combo"].currentData() or "",
            misc_tags=self.misc_tags_widget.get_included(),
            genre_tags=self.genre_tags_widget.get_included(),
            excluded_misc_tags=self.misc_tags_widget.get_excluded(),
            excluded_genre_tags=self.genre_tags_widget.get_excluded(),
        )

    def clear_filters(self) -> None:
        self.sort_combo["combo"].setCurrentIndex(0)
        self.category_combo["combo"].setCurrentIndex(0)
        self.type_combo["combo"].setCurrentIndex(0)
        self.age_combo["combo"].setCurrentIndex(0)
        self.resolution_combo["combo"].setCurrentIndex(0)
        self._sort_order = "desc"
        self.sort_order_button.setChecked(False)
        self.sort_order_button.setText("↓")
        self.misc_tags_widget.reset_all()
        self.genre_tags_widget.reset_all()


class UnifiedFilterBar(QWidget):
    MODE_WORKSHOP = "workshop"
    MODE_LOCAL = "local"

    filters_changed = pyqtSignal(object)
    refresh_requested = pyqtSignal(object)
    search_requested = pyqtSignal(str)

    def __init__(self, theme_manager, translator, mode: str, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self.tr = translator
        self.mode = mode
        self._current_page = 1

        self._setup_ui()
        self._setup_popups()

    def _setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        search_mode = (
            SearchPanel.SEARCH_MODE_MANUAL
            if self.mode == self.MODE_WORKSHOP
            else SearchPanel.SEARCH_MODE_LIVE
        )

        self.search_panel = SearchPanel(self.theme, self.tr, search_mode, self)

        if self.mode == self.MODE_WORKSHOP:
            self.search_panel.search_button.clicked.connect(
                lambda: self._on_search_requested(self.search_panel.text())
            )
            self.search_panel.search_input.returnPressed.connect(
                lambda: self._on_search_requested(self.search_panel.text())
            )
        else:
            self.search_panel.search_input.textChanged.connect(lambda _text: self._emit_filters())
            self.search_panel.search_button.clicked.connect(lambda: self._emit_filters())
            self.search_panel.search_input.returnPressed.connect(lambda: self._emit_filters())

        self.search_panel.filter_button.clicked.connect(self._toggle_filters_popup)
        self.search_panel.actions_button.clicked.connect(self._toggle_actions_popup)

        root.addWidget(self.search_panel)

    def _setup_popups(self) -> None:
        if self.mode == self.MODE_WORKSHOP:
            self.filters_popup = WorkshopFiltersPanel(self.theme, self.tr, self)
        else:
            self.filters_popup = LocalFiltersPanel(self.theme, self.tr, self)

        self.actions_popup = UnifiedActionsPanel(self.theme, self.tr, self)

        self.filters_popup.hide()
        self.actions_popup.hide()

        self.filters_popup.closed.connect(self._on_popup_closed)
        self.actions_popup.closed.connect(self._on_popup_closed)

        self.filters_popup.filters_changed.connect(self._emit_filters)
        self.actions_popup.clear_requested.connect(self._on_clear_requested)
        self.actions_popup.refresh_requested.connect(self._on_refresh_requested)

    def _on_popup_closed(self) -> None:
        self.search_panel.set_filter_active(False)
        self.search_panel.set_actions_active(False)

    def set_page(self, page: int) -> None:
        self._current_page = page

    def set_info_text(self, text: str) -> None:
        self.search_panel.set_info_texts(primary=text)

    def set_info_texts(self, primary: str = "", secondary: str = "") -> None:
        self.search_panel.set_info_texts(primary, secondary)

    def _toggle_filters_popup(self) -> None:
        if self.actions_popup.isVisible():
            self.actions_popup.hide_and_emit()

        if self.filters_popup.isVisible():
            self.filters_popup.hide_and_emit()
            return

        self.filters_popup.adjustSize()
        self.search_panel.set_filter_active(True)
        self.search_panel.set_actions_active(False)
        anchor = self.search_panel.filter_anchor()
        self.filters_popup.show_right_of(anchor, x_gap=-12, y_offset=-8)

    def _toggle_actions_popup(self) -> None:
        if self.filters_popup.isVisible():
            self.filters_popup.hide_and_emit()

        if self.actions_popup.isVisible():
            self.actions_popup.hide_and_emit()
            return

        self.actions_popup.adjustSize()
        self.search_panel.set_actions_active(True)
        self.search_panel.set_filter_active(False)
        anchor = self.search_panel.actions_anchor()
        self.actions_popup.show_right_of(anchor, x_gap=-12, y_offset=-7)

    def _on_search_requested(self, text: str) -> None:
        self.search_requested.emit(text)
        self._emit_filters()

    def _on_clear_requested(self) -> None:
        self.search_panel.clear()
        if self.mode == self.MODE_WORKSHOP:
            self._current_page = 1

        self.filters_popup.clear_filters()
        self.refresh_requested.emit(self.get_current_filters())

    def _on_refresh_requested(self) -> None:
        self.refresh_requested.emit(self.get_current_filters())

    def _emit_filters(self) -> None:
        self.filters_changed.emit(self.get_current_filters())

    def get_current_filters(self):
        if self.mode == self.MODE_WORKSHOP:
            return self.filters_popup.get_filters(self.search_panel.text(), self._current_page)
        return self.filters_popup.get_filters(self.search_panel.text())
from dataclasses import dataclass, field
from typing import Any

from PyQt6.QtCore import Qt, QRectF, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from domain.config.workshop_filter_config import WorkshopFilterConfig
from ui.widgets.animated_container import AnimatedContainer


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


class StateTagCheckBoxLocal(QCheckBox):
    state_changed_tri = pyqtSignal()

    def __init__(self, text: str, theme_manager, parent=None):
        super().__init__(text, parent)
        self.theme = theme_manager
        self._tri_state = 0

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_right_click)

        self._apply_style()

    def tri_state(self) -> int:
        return self._tri_state

    def reset(self) -> None:
        self._tri_state = 0
        self.setChecked(False)
        self._apply_style()

    def nextCheckState(self):
        if self._tri_state == 0:
            self._tri_state = 1
            self.setChecked(True)
        else:
            self._tri_state = 0
            self.setChecked(False)

        self._apply_style()
        self.state_changed_tri.emit()

    def _on_right_click(self):
        if self._tri_state == 2:
            self._tri_state = 0
            self.setChecked(False)
        else:
            self._tri_state = 2
            self.setChecked(True)

        self._apply_style()
        self.state_changed_tri.emit()

    def _apply_style(self) -> None:
        if self._tri_state == 2:
            bg = "#c0392b"
            border = "#c0392b"
        elif self._tri_state == 1:
            bg = self.theme.get_color("primary")
            border = self.theme.get_color("primary")
        else:
            bg = self.theme.get_color("bg_tertiary")
            border = self.theme.get_color("border")

        self.setStyleSheet(
            f"""
            QCheckBox {{
                color: {self.theme.get_color('text_primary')};
                font-size: 10px;
                spacing: 3px;
            }}

            QCheckBox::indicator {{
                width: 12px;
                height: 12px;
                border-radius: 2px;
                border: 1px solid {border};
                background: {bg};
            }}
            """
        )


class LocalFilterBar(QWidget):
    filters_changed = pyqtSignal(object)
    refresh_requested = pyqtSignal()

    def __init__(self, theme_manager, translator, parent=None):
        super().__init__(parent)

        self.theme = theme_manager
        self.tr = translator
        self._current_filters = LocalFilters()

        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 10)
        main_layout.setSpacing(4)

        row1 = self._create_row1()
        main_layout.addWidget(row1)

        row2 = self._create_row2()
        main_layout.addWidget(row2)

        self.tags_animated = AnimatedContainer(self)
        self.tags_container = self._create_tags_section()
        self.tags_animated.set_content_widget(self.tags_container)
        main_layout.addWidget(self.tags_animated)

    def _create_row1(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {self.theme.get_color('bg_secondary')};
                border-radius: 8px;
                padding: 0px;
            }}
            """
        )

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr.t("labels.search_placeholder"))
        self.search_input.setFixedWidth(200)
        self.search_input.setFixedHeight(26)
        self.search_input.setStyleSheet(self._input_style())
        self.search_input.textChanged.connect(self._emit_filters)
        layout.addWidget(self.search_input)

        search_icon = QLabel()
        search_icon.setText("⌕")
        search_icon.setFixedSize(26, 26)
        search_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        search_icon.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(search_icon)

        layout.addSpacing(10)
        layout.addWidget(self._label(self.tr.t("labels.sort")))

        self.sort_combo = self._create_combo(
            LocalFilterConfig.get_translated_sort_options(self.tr.t),
            120,
        )
        self.sort_combo.currentTextChanged.connect(self._emit_filters)
        layout.addWidget(self.sort_combo)

        layout.addStretch()

        self.expand_btn = QPushButton(self.tr.t("labels.more_filters"))
        self.expand_btn.setFixedSize(100, 26)
        self.expand_btn.setStyleSheet(self._button_style("#5B8DEF"))
        self.expand_btn.clicked.connect(self._toggle_expanded)
        layout.addWidget(self.expand_btn)

        return frame

    def _create_row2(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {self.theme.get_color('bg_secondary')};
                border-radius: 10px;
            }}
            """
        )

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(10)

        layout.addWidget(self._label(self.tr.t("labels.category")))
        self.category_combo = self._create_combo(
            WorkshopFilterConfig.get_translated_categories(self.tr.t),
            100,
        )
        self.category_combo.currentTextChanged.connect(self._emit_filters)
        layout.addWidget(self.category_combo)

        layout.addWidget(self._label(self.tr.t("labels.type")))
        self.type_combo = self._create_combo(
            WorkshopFilterConfig.get_translated_types(self.tr.t),
            100,
        )
        self.type_combo.currentTextChanged.connect(self._emit_filters)
        layout.addWidget(self.type_combo)

        layout.addWidget(self._label(self.tr.t("labels.age")))
        self.age_combo = self._create_combo(
            WorkshopFilterConfig.get_translated_age_ratings(self.tr.t),
            100,
        )
        self.age_combo.currentTextChanged.connect(self._emit_filters)
        layout.addWidget(self.age_combo)

        layout.addWidget(self._label(self.tr.t("labels.resolution")))
        self.resolution_combo = self._create_combo(
            WorkshopFilterConfig.get_translated_resolutions(self.tr.t),
            110,
        )
        self.resolution_combo.currentTextChanged.connect(self._emit_filters)
        layout.addWidget(self.resolution_combo)

        layout.addStretch()

        clear_btn = QPushButton(self.tr.t("labels.clear"))
        clear_btn.setFixedSize(65, 24)
        clear_btn.setStyleSheet(self._button_style("#666"))
        clear_btn.clicked.connect(self._clear_filters)
        layout.addWidget(clear_btn)

        return frame

    def _create_tags_section(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {self.theme.get_color('bg_secondary')};
                border-radius: 10px;
            }}
            """
        )

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(4)

        misc_frame = QFrame()
        misc_layout = QHBoxLayout(misc_frame)
        misc_layout.setContentsMargins(0, 0, 0, 0)
        misc_layout.setSpacing(6)
        misc_layout.addWidget(self._label(self.tr.t("labels.miscellaneous"), bold=True))

        misc_scroll = QScrollArea()
        misc_scroll.setWidgetResizable(True)
        misc_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        misc_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        misc_scroll.setFixedHeight(26)
        misc_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        misc_content = QWidget()
        misc_content_layout = QHBoxLayout(misc_content)
        misc_content_layout.setContentsMargins(0, 0, 0, 0)
        misc_content_layout.setSpacing(4)

        self.misc_checkboxes: dict[str, StateTagCheckBoxLocal] = {}
        misc_translations = WorkshopFilterConfig.get_translated_misc_tags(self.tr.t)

        for tag in WorkshopFilterConfig.MISC_TAG_KEYS:
            translated_tag = misc_translations.get(tag, tag)
            checkbox = StateTagCheckBoxLocal(translated_tag, self.theme)
            checkbox.state_changed_tri.connect(self._emit_filters)
            self.misc_checkboxes[tag] = checkbox
            misc_content_layout.addWidget(checkbox)

        misc_scroll.setWidget(misc_content)
        misc_layout.addWidget(misc_scroll, 1)
        layout.addWidget(misc_frame)

        genre_frame = QFrame()
        genre_layout = QHBoxLayout(genre_frame)
        genre_layout.setContentsMargins(0, 0, 0, 0)
        genre_layout.setSpacing(6)
        genre_layout.addWidget(self._label(self.tr.t("labels.genre"), bold=True))

        genre_scroll = QScrollArea()
        genre_scroll.setWidgetResizable(True)
        genre_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        genre_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        genre_scroll.setFixedHeight(26)
        genre_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        genre_content = QWidget()
        genre_content_layout = QHBoxLayout(genre_content)
        genre_content_layout.setContentsMargins(0, 0, 0, 0)
        genre_content_layout.setSpacing(4)

        self.genre_checkboxes: dict[str, StateTagCheckBoxLocal] = {}
        genre_translations = WorkshopFilterConfig.get_translated_genre_tags(self.tr.t)

        for tag in WorkshopFilterConfig.GENRE_TAG_KEYS:
            translated_tag = genre_translations.get(tag, tag)
            checkbox = StateTagCheckBoxLocal(translated_tag, self.theme)
            checkbox.state_changed_tri.connect(self._emit_filters)
            self.genre_checkboxes[tag] = checkbox
            genre_content_layout.addWidget(checkbox)

        genre_scroll.setWidget(genre_content)
        genre_layout.addWidget(genre_scroll, 1)
        layout.addWidget(genre_frame)

        return frame

    def _create_combo(self, options: dict[str, str], width: int) -> QComboBox:
        combo = QComboBox()
        combo.setFixedWidth(width)
        combo.setStyleSheet(self._combo_style())

        for value, label in options.items():
            combo.addItem(label, value)

        return combo

    def _label(self, text: str, bold: bool = False) -> QLabel:
        label = QLabel(text)
        weight = "600" if bold else "normal"
        label.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_secondary')};
            font-weight: {weight};
            font-size: 12px;
            background: transparent;
            """
        )
        return label

    def _input_style(self) -> str:
        return f"""
        QLineEdit {{
            background-color: {self.theme.get_color('bg_tertiary')};
            border: 1px solid {self.theme.get_color('border')};
            border-radius: 4px;
            padding: 2px 8px;
            color: {self.theme.get_color('text_primary')};
            font-size: 11px;
        }}

        QLineEdit:focus {{
            border-color: {self.theme.get_color('primary')};
        }}
        """

    def _combo_style(self) -> str:
        return f"""
        QComboBox {{
            background-color: {self.theme.get_color('bg_tertiary')};
            color: {self.theme.get_color('text_primary')};
            border: 1px solid {self.theme.get_color('border')};
            border-radius: 4px;
            padding: 2px 6px;
            font-size: 11px;
            min-height: 20px;
        }}

        QComboBox::drop-down {{
            border: none;
            width: 16px;
        }}

        QComboBox QAbstractItemView {{
            background-color: {self.theme.get_color('bg_elevated')};
            color: {self.theme.get_color('text_primary')};
            selection-background-color: {self.theme.get_color('primary')};
            border: 1px solid {self.theme.get_color('border')};
            border-radius: 4px;
        }}
        """

    def _button_style(self, color: str | None = None) -> str:
        button_color = color or self.theme.get_color("primary")
        return f"""
        QPushButton {{
            background-color: {button_color};
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            font-size: 11px;
            padding: 0px;
        }}

        QPushButton:hover {{
            background-color: {self.theme.get_color('primary_hover')};
        }}
        """

    def _toggle_expanded(self) -> None:
        expanding = not self.tags_animated.is_expanded()
        self.tags_animated.toggle(expanding)
        self.expand_btn.setText(
            self.tr.t("labels.less_filters") if expanding else self.tr.t("labels.more_filters")
        )

    def _clear_filters(self) -> None:
        self.search_input.clear()
        self.sort_combo.setCurrentIndex(0)
        self.category_combo.setCurrentIndex(0)
        self.type_combo.setCurrentIndex(0)
        self.age_combo.setCurrentIndex(0)
        self.resolution_combo.setCurrentIndex(0)
        self._current_filters.sort_order = "desc"

        for checkbox in self.misc_checkboxes.values():
            checkbox.reset()

        for checkbox in self.genre_checkboxes.values():
            checkbox.reset()

        self.refresh_requested.emit()

    def _emit_filters(self) -> None:
        self.filters_changed.emit(self.get_current_filters())

    def get_current_filters(self) -> LocalFilters:
        misc_tags = [tag for tag, checkbox in self.misc_checkboxes.items() if checkbox.tri_state() == 1]
        excluded_misc = [tag for tag, checkbox in self.misc_checkboxes.items() if checkbox.tri_state() == 2]
        genre_tags = [tag for tag, checkbox in self.genre_checkboxes.items() if checkbox.tri_state() == 1]
        excluded_genre = [tag for tag, checkbox in self.genre_checkboxes.items() if checkbox.tri_state() == 2]

        return LocalFilters(
            search=self.search_input.text().strip(),
            sort=self.sort_combo.currentData() or "install_date",
            sort_order=self._current_filters.sort_order,
            category=self.category_combo.currentData() or "",
            type_tag=self.type_combo.currentData() or "",
            age_rating=self.age_combo.currentData() or "",
            resolution=self.resolution_combo.currentData() or "",
            misc_tags=misc_tags,
            genre_tags=genre_tags,
            excluded_misc_tags=excluded_misc,
            excluded_genre_tags=excluded_genre,
        )
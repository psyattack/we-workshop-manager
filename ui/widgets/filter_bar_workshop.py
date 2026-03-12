from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget

from domain.config.workshop_filter_config import WorkshopFilterConfig
from domain.models.workshop import WorkshopFilters
from infrastructure.resources.resource_manager import get_icon
from ui.widgets.animated_container import AnimatedContainer
from ui.widgets.filter_bar_local import StateTagCheckBoxLocal


class CompactFilterBar(QWidget):
    filters_changed = pyqtSignal(WorkshopFilters)
    refresh_requested = pyqtSignal(WorkshopFilters)
    search_requested = pyqtSignal(str)

    def __init__(self, theme_manager, translator, parent=None):
        super().__init__(parent)

        self.theme = theme_manager
        self.tr = translator
        self._current_filters = WorkshopFilters()

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
        self.search_input.returnPressed.connect(self._on_search)
        layout.addWidget(self.search_input)

        search_btn = QPushButton()
        search_btn.setToolTip(self.tr.t("tooltips.search"))
        search_btn.setIcon(get_icon("ICON_SEARCH"))
        search_btn.setIconSize(QSize(18, 18))
        search_btn.setFixedSize(26, 26)
        search_btn.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border-radius: 6px;
                border: none;
            }

            QPushButton:hover {
                background-color: rgba(78, 140, 255, 0.25);
            }
            """
        )
        search_btn.clicked.connect(self._on_search)
        layout.addWidget(search_btn)

        layout.addSpacing(10)
        layout.addWidget(self._label(self.tr.t("labels.sort")))

        self.sort_combo = self._create_combo(
            WorkshopFilterConfig.get_translated_sort_options(self.tr.t),
            130,
        )
        self.sort_combo.currentTextChanged.connect(self._on_sort_changed)
        layout.addWidget(self.sort_combo)

        layout.addWidget(self._label(self.tr.t("labels.period")))
        self.time_combo = self._create_combo(
            WorkshopFilterConfig.get_translated_time_periods(self.tr.t),
            100,
        )
        self.time_combo.setCurrentIndex(1)
        self.time_combo.currentTextChanged.connect(self._emit_filters)
        layout.addWidget(self.time_combo)

        layout.addStretch()

        self.expand_btn = QPushButton(self.tr.t("labels.more_filters"))
        self.expand_btn.setFixedSize(100, 26)
        self.expand_btn.setStyleSheet(self._button_style("#5B8DEF"))
        self.expand_btn.clicked.connect(self._toggle_expanded)
        layout.addWidget(self.expand_btn)

        refresh_btn = QPushButton()
        refresh_btn.setToolTip(self.tr.t("tooltips.refresh"))
        refresh_btn.setIcon(get_icon("ICON_REFRASH"))
        refresh_btn.setIconSize(QSize(18, 18))
        refresh_btn.setFixedSize(26, 26)
        refresh_btn.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border-radius: 6px;
                border: none;
            }

            QPushButton:hover {
                background-color: rgba(78, 140, 255, 0.25);
            }
            """
        )
        refresh_btn.clicked.connect(self._on_refresh)
        layout.addWidget(refresh_btn)

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

        combo_frame = QFrame()
        combo_layout = QHBoxLayout(combo_frame)
        combo_layout.setContentsMargins(0, 0, 0, 0)
        combo_layout.setSpacing(10)

        combo_layout.addWidget(self._label(self.tr.t("labels.asset_type")))
        self.asset_type_combo = self._create_combo(
            WorkshopFilterConfig.get_translated_asset_types(self.tr.t),
            110,
        )
        self.asset_type_combo.currentTextChanged.connect(self._emit_filters)
        combo_layout.addWidget(self.asset_type_combo)

        combo_layout.addWidget(self._label(self.tr.t("labels.asset_genre")))
        self.asset_genre_combo = self._create_combo(
            WorkshopFilterConfig.get_translated_asset_genres(self.tr.t),
            130,
        )
        self.asset_genre_combo.currentTextChanged.connect(self._emit_filters)
        combo_layout.addWidget(self.asset_genre_combo)

        combo_layout.addWidget(self._label(self.tr.t("labels.script_type")))
        self.script_type_combo = self._create_combo(
            WorkshopFilterConfig.get_translated_script_types(self.tr.t),
            120,
        )
        self.script_type_combo.currentTextChanged.connect(self._emit_filters)
        combo_layout.addWidget(self.script_type_combo)

        combo_layout.addStretch()
        layout.addWidget(combo_frame)

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

        incompatible_frame = QFrame()
        incompatible_layout = QHBoxLayout(incompatible_frame)
        incompatible_layout.setContentsMargins(0, 0, 0, 0)
        incompatible_layout.setSpacing(6)

        incompatible_layout.addWidget(self._label(self.tr.t("labels.other"), bold=True))

        self.incompatible_checkbox = QCheckBox(self.tr.t("labels.incompatible_items"))
        self.incompatible_checkbox.setStyleSheet(self._checkbox_style())
        self.incompatible_checkbox.setToolTip(self.tr.t("tooltips_extended.incompatible_items"))
        self.incompatible_checkbox.stateChanged.connect(self._emit_filters)

        incompatible_layout.addWidget(self.incompatible_checkbox)
        incompatible_layout.addStretch()

        layout.addWidget(incompatible_frame)

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

    def _checkbox_style(self) -> str:
        return f"""
        QCheckBox {{
            color: {self.theme.get_color('text_primary')};
            font-size: 10px;
            spacing: 3px;
        }}

        QCheckBox::indicator {{
            width: 12px;
            height: 12px;
            border-radius: 2px;
            border: 1px solid {self.theme.get_color('border')};
            background: {self.theme.get_color('bg_tertiary')};
        }}

        QCheckBox::indicator:checked {{
            background: {self.theme.get_color('primary')};
            border-color: {self.theme.get_color('primary')};
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

    def _on_sort_changed(self) -> None:
        is_trend = self.sort_combo.currentData() == "trend"
        self.time_combo.setEnabled(is_trend)
        self._emit_filters()

    def _on_search(self) -> None:
        self._emit_filters()

    def _clear_filters(self) -> None:
        self.search_input.clear()
        self.sort_combo.setCurrentIndex(0)
        self.time_combo.setCurrentIndex(1)
        self.category_combo.setCurrentIndex(0)
        self.type_combo.setCurrentIndex(0)
        self.age_combo.setCurrentIndex(0)
        self.resolution_combo.setCurrentIndex(0)

        for checkbox in self.misc_checkboxes.values():
            checkbox.reset()

        for checkbox in self.genre_checkboxes.values():
            checkbox.reset()

        self.asset_type_combo.setCurrentIndex(0)
        self.asset_genre_combo.setCurrentIndex(0)
        self.script_type_combo.setCurrentIndex(0)
        self.incompatible_checkbox.setChecked(False)

        filters = self.get_current_filters()
        self.refresh_requested.emit(filters)

    def _on_refresh(self) -> None:
        self.refresh_requested.emit(self.get_current_filters())

    def _emit_filters(self) -> None:
        self.filters_changed.emit(self.get_current_filters())

    def get_current_filters(self) -> WorkshopFilters:
        misc_tags = [tag for tag, checkbox in self.misc_checkboxes.items() if checkbox.tri_state() == 1]
        excluded_misc = [tag for tag, checkbox in self.misc_checkboxes.items() if checkbox.tri_state() == 2]
        genre_tags = [tag for tag, checkbox in self.genre_checkboxes.items() if checkbox.tri_state() == 1]
        excluded_genre = [tag for tag, checkbox in self.genre_checkboxes.items() if checkbox.tri_state() == 2]

        required_flags = []
        if self.incompatible_checkbox.isChecked():
            required_flags.append("incompatible")

        return WorkshopFilters(
            search=self.search_input.text().strip(),
            sort=self.sort_combo.currentData() or "trend",
            days=self.time_combo.currentData() or "7",
            category=self.category_combo.currentData() or "",
            type_tag=self.type_combo.currentData() or "",
            age_rating=self.age_combo.currentData() or "",
            resolution=self.resolution_combo.currentData() or "",
            misc_tags=misc_tags,
            genre_tags=genre_tags,
            excluded_misc_tags=excluded_misc,
            excluded_genre_tags=excluded_genre,
            asset_type=self.asset_type_combo.currentData() or "",
            asset_genre=self.asset_genre_combo.currentData() or "",
            script_type=self.script_type_combo.currentData() or "",
            required_flags=required_flags,
            page=self._current_filters.page,
        )

    def set_page(self, page: int) -> None:
        self._current_filters.page = page
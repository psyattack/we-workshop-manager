from typing import Dict
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QLineEdit, QPushButton, QScrollArea, QFrame, QCheckBox
)
from core.workshop_filters import FilterConfig, WorkshopFilters
from resources.icons import get_icon

class CompactFilterBar(QWidget):
    filters_changed = pyqtSignal(WorkshopFilters)
    search_requested = pyqtSignal(str)
    
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self.config = FilterConfig()
        self._current_filters = WorkshopFilters()
        self._setup_ui()
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)
        
        row1 = self._create_row1()
        main_layout.addWidget(row1)

        row2 = self._create_row2()
        main_layout.addWidget(row2)

        self.tags_container = self._create_tags_section()
        self.tags_container.hide()
        main_layout.addWidget(self.tags_container)
    
    def _create_row1(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.get_color('bg_secondary')};
                border-radius: 8px;
                padding: 0px;
            }}
        """)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(8)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.setFixedWidth(200)
        self.search_input.setFixedHeight(26)
        self.search_input.setStyleSheet(self._input_style())
        self.search_input.returnPressed.connect(self._on_search)
        layout.addWidget(self.search_input)
        
        search_btn = QPushButton()
        search_btn.setToolTip("Search")
        search_btn.setIcon(get_icon("ICON_SEARCH"))
        search_btn.setIconSize(QSize(18, 18))
        search_btn.setFixedSize(26, 26)
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(78, 140, 255, 0.25);
            }
        """)
        search_btn.clicked.connect(self._on_search)
        layout.addWidget(search_btn)
        
        layout.addSpacing(10)
        
        layout.addWidget(self._label("Sort:"))
        self.sort_combo = self._create_combo(self.config.SORT_OPTIONS, 130)
        self.sort_combo.currentTextChanged.connect(self._on_sort_changed)
        layout.addWidget(self.sort_combo)

        layout.addWidget(self._label("Period:"))
        self.time_combo = self._create_combo(self.config.TIME_PERIODS, 100)
        self.time_combo.setCurrentIndex(1)
        self.time_combo.currentTextChanged.connect(self._emit_filters)
        layout.addWidget(self.time_combo)
        
        layout.addStretch()
        
        self.expand_btn = QPushButton("▼ More Filters")
        self.expand_btn.setFixedSize(100, 26)
        self.expand_btn.setStyleSheet(self._button_style("#5B8DEF"))
        self.expand_btn.clicked.connect(self._toggle_expanded)
        layout.addWidget(self.expand_btn)
        
        refresh_btn = QPushButton()
        refresh_btn.setToolTip("Refresh")
        refresh_btn.setIcon(get_icon("ICON_REFRASH"))
        refresh_btn.setIconSize(QSize(18, 18))
        refresh_btn.setFixedSize(26, 26)
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border-radius: 6px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(78, 140, 255, 0.25);
            }
        """)
        refresh_btn.clicked.connect(self._emit_filters)
        layout.addWidget(refresh_btn)
        
        return frame
    
    def _create_row2(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.get_color('bg_secondary')};
                border-radius: 10px;
            }}
        """)
        
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(10)

        layout.addWidget(self._label("Category:"))
        self.category_combo = self._create_combo(self.config.CATEGORIES, 100)
        self.category_combo.currentTextChanged.connect(self._emit_filters)
        layout.addWidget(self.category_combo)

        layout.addWidget(self._label("Type:"))
        self.type_combo = self._create_combo(self.config.TYPES, 100)
        self.type_combo.currentTextChanged.connect(self._emit_filters)
        layout.addWidget(self.type_combo)
        
        layout.addWidget(self._label("Age:"))
        self.age_combo = self._create_combo(self.config.AGE_RATINGS, 100)
        self.age_combo.currentTextChanged.connect(self._emit_filters)
        layout.addWidget(self.age_combo)

        layout.addWidget(self._label("Resolution:"))
        self.resolution_combo = self._create_combo(self.config.RESOLUTIONS, 110)
        self.resolution_combo.currentTextChanged.connect(self._emit_filters)
        layout.addWidget(self.resolution_combo)
        
        layout.addStretch()
        
        clear_btn = QPushButton("✕ Clear")
        clear_btn.setFixedSize(65, 24)
        clear_btn.setStyleSheet(self._button_style("#666"))
        clear_btn.clicked.connect(self._clear_filters)
        layout.addWidget(clear_btn)
        
        return frame
    
    def _create_tags_section(self) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
        QFrame {{
            background-color: {self.theme.get_color('bg_secondary')};
            border-radius: 10px;
        }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(4)

        misc_frame = QFrame()
        misc_layout = QHBoxLayout(misc_frame)
        misc_layout.setContentsMargins(0, 0, 0, 0)
        misc_layout.setSpacing(6)
        misc_layout.addWidget(self._label("Features:", bold=True))
        self.misc_checkboxes = {}
        for tag in self.config.MISC_TAGS[:6]:
            cb = QCheckBox(tag)
            cb.setStyleSheet(self._checkbox_style())
            cb.stateChanged.connect(self._emit_filters)
            self.misc_checkboxes[tag] = cb
            misc_layout.addWidget(cb)
        misc_layout.addStretch()
        layout.addWidget(misc_frame)
        
        genre_frame = QFrame()
        genre_layout = QHBoxLayout(genre_frame)
        genre_layout.setContentsMargins(0, 0, 0, 0)
        genre_layout.setSpacing(6)
        
        genre_layout.addWidget(self._label("Genre:", bold=True))
        
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
        
        self.genre_checkboxes = {}
        for tag in self.config.GENRE_TAGS:
            cb = QCheckBox(tag)
            cb.setStyleSheet(self._checkbox_style())
            cb.stateChanged.connect(self._emit_filters)
            self.genre_checkboxes[tag] = cb
            genre_content_layout.addWidget(cb)
        
        genre_scroll.setWidget(genre_content)
        genre_layout.addWidget(genre_scroll, 1)
        
        layout.addWidget(genre_frame)

        incompatible_frame = QFrame()
        incompatible_layout = QHBoxLayout(incompatible_frame)
        incompatible_layout.setContentsMargins(0, 0, 0, 0)
        incompatible_layout.setSpacing(6)
        
        self.incompatible_checkbox = QCheckBox("Incompatible items")
        self.incompatible_checkbox.setStyleSheet(self._checkbox_style())
        self.incompatible_checkbox.setToolTip("Some items cannot be included in the game. However, you can find them by checking the box here.")
        self.incompatible_checkbox.stateChanged.connect(self._emit_filters)
        incompatible_layout.addWidget(self.incompatible_checkbox)
        incompatible_layout.addStretch()
        
        layout.addWidget(incompatible_frame)
        
        return frame
    
    def _create_combo(self, options: Dict[str, str], width: int) -> QComboBox:
        combo = QComboBox()
        combo.setFixedWidth(width)
        combo.setStyleSheet(self._combo_style())
        
        for value, label in options.items():
            combo.addItem(label, value)
        
        return combo
    
    def _label(self, text: str, bold: bool = False) -> QLabel:
        label = QLabel(text)
        weight = "600" if bold else "normal"
        label.setStyleSheet(f"""
            color: {self.theme.get_color('text_secondary')};
            font-weight: {weight};
            font-size: 12px;
            background: transparent;
        """)
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
            QComboBox::drop-down {{ border: none; width: 16px; }}
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
    
    def _button_style(self, color: str = None) -> str:
        c = color or self.theme.get_color('primary')
        return f"""
            QPushButton {{
                background-color: {c};
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
    
    def _toggle_expanded(self):
        if self.tags_container.isVisible():
            self.tags_container.hide()
            self.expand_btn.setText("▼ More Filters")
        else:
            self.tags_container.show()
            self.expand_btn.setText("▲ Less Filters")
    
    def _on_sort_changed(self):
        is_trend = self.sort_combo.currentData() == "trend"
        self.time_combo.setEnabled(is_trend)
        self._emit_filters()
    
    def _on_search(self):
        self._emit_filters()
    
    def _clear_filters(self):
        self.search_input.clear()
        self.sort_combo.setCurrentIndex(0)
        self.time_combo.setCurrentIndex(1)
        self.category_combo.setCurrentIndex(0)
        self.type_combo.setCurrentIndex(0)
        self.age_combo.setCurrentIndex(0)
        self.resolution_combo.setCurrentIndex(0)
        
        for cb in self.misc_checkboxes.values():
            cb.setChecked(False)
        for cb in self.genre_checkboxes.values():
            cb.setChecked(False)

        self.incompatible_checkbox.setChecked(False)
        self._emit_filters()
    
    def _emit_filters(self):
        filters = self.get_current_filters()
        self.filters_changed.emit(filters)
    
    def get_current_filters(self) -> WorkshopFilters:
        misc_tags = [tag for tag, cb in self.misc_checkboxes.items() if cb.isChecked()]
        genre_tags = [tag for tag, cb in self.genre_checkboxes.items() if cb.isChecked()]
        
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
            required_flags=required_flags,
            page=self._current_filters.page
        )
    
    def set_page(self, page: int):
        self._current_filters.page = page

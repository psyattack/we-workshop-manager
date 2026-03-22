from PyQt6.QtCore import QEvent, QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QWidget

from infrastructure.resources.resource_manager import get_icon
from ui.widgets.browse_toggle import BrowseToggle
from ui.widgets.custom_tooltip import install_tooltip


class SearchPanel(QWidget):
    SEARCH_MODE_MANUAL = "manual"
    SEARCH_MODE_LIVE = "live"
    FIXED_SEARCH_WIDTH = 250
    author_close_requested = pyqtSignal()
    browse_mode_changed = pyqtSignal(int)

    def __init__(self, theme_manager, translator, search_mode: str = "manual", parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self.tr = translator
        self.search_mode = search_mode

        self._filter_active = False
        self._actions_active = False

        self._search_hovered = False
        self._filter_hovered = False
        self._actions_hovered = False

        self._setup_ui()

    def _setup_ui(self) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(8)

        self.browse_toggle = BrowseToggle(
            [self.tr.t("labels.author_workshop_files"),
             self.tr.t("labels.author_collections")],
            self.theme, self,
        )
        self.browse_toggle.setFixedHeight(36)
        self.browse_toggle.currentChanged.connect(self.browse_mode_changed.emit)

        root.addWidget(self.browse_toggle)
        root.addSpacing(0)

        self.info_primary_frame = self._create_info_box()
        self.info_secondary_frame = self._create_info_box()

        root.addWidget(self.info_primary_frame)
        root.addWidget(self.info_secondary_frame)

        self.search_host = QWidget()
        self.search_host.setObjectName("searchPanelHost")
        search_host_layout = QHBoxLayout(self.search_host)
        search_host_layout.setContentsMargins(0, 0, 0, 0)
        search_host_layout.setSpacing(8)

        self.main_frame = QFrame()
        self.main_frame.setObjectName("searchPanelMainFrame")
        self.main_frame.setFixedHeight(36)
        self.main_frame.setFixedWidth(self.FIXED_SEARCH_WIDTH)
        self.main_frame.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.main_frame.installEventFilter(self)

        frame_layout = QHBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(6, 0, 0, 0)
        frame_layout.setSpacing(0)

        self.search_button = QPushButton()
        self.search_button.setFixedSize(30, 30)
        self.search_button.setIcon(get_icon("ICON_SEARCH"))
        self.search_button.setIconSize(QSize(20, 20))
        self.search_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.search_button.setObjectName("searchPanelSearchButton")
        install_tooltip(self.search_button, self.tr.t("tooltips.search"), "bottom", self.theme)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr.t("labels.search_placeholder"))
        self.search_input.setFrame(False)
        self.search_input.setFixedHeight(30)
        self.search_input.setObjectName("searchPanelLineEdit")
        self.search_input.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        self.search_input.installEventFilter(self)

        self.filter_button = QPushButton()
        self.filter_button.setFixedSize(36, 36)
        self.filter_button.setIcon(get_icon("ICON_FILTER"))
        self.filter_button.setIconSize(QSize(24, 24))
        self.filter_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.filter_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.filter_button.setObjectName("searchPanelFilterButton")
        self.filter_button.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.filter_button.installEventFilter(self)

        self.actions_button = QPushButton()
        self.actions_button.setFixedSize(36, 36)
        self.actions_button.setIcon(get_icon("ICON_ELLIPSIS"))
        self.actions_button.setIconSize(QSize(15, 15))
        self.actions_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.actions_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.actions_button.setObjectName("searchPanelActionsButton")
        self.actions_button.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.actions_button.installEventFilter(self)

        frame_layout.addWidget(self.search_button)
        frame_layout.addWidget(self.search_input, 1)
        frame_layout.addWidget(self.filter_button)

        search_host_layout.addWidget(self.main_frame)
        search_host_layout.addWidget(self.actions_button)

        root.addWidget(self.search_host)
        self._apply_styles()

    def _create_info_box(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("searchPanelInfoBox")
        frame.setFixedHeight(36)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(12, 0, 6, 0)
        layout.setSpacing(4)

        label = QLabel("")
        label.setObjectName("searchPanelInfoLabel")
        layout.addWidget(label, 1)

        close_btn = QPushButton()
        close_btn.setFixedSize(20, 20)
        close_btn.setIcon(get_icon("ICON_CLOSE2"))
        close_btn.setIconSize(QSize(10, 10))
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        close_btn.setObjectName("infoCloseBtn")
        close_btn.clicked.connect(self.author_close_requested.emit)
        close_btn.hide()
        layout.addWidget(close_btn)

        frame._label = label
        frame._close_btn = close_btn
        frame.hide()
        return frame

    def eventFilter(self, obj, event):
        event_type = event.type()

        if obj == self.main_frame or obj == self.search_input:
            if event_type == QEvent.Type.Enter:
                if not self.filter_button.underMouse():
                    self._search_hovered = True
                    self._apply_styles()
            elif event_type == QEvent.Type.Leave:
                if not self.main_frame.underMouse() and not self.search_input.underMouse():
                    self._search_hovered = False
                    self._apply_styles()

        elif obj == self.filter_button:
            if event_type == QEvent.Type.Enter:
                self._filter_hovered = True
                self._search_hovered = False
                self._apply_styles()
            elif event_type == QEvent.Type.Leave:
                self._filter_hovered = False
                if self.main_frame.underMouse() and not self.filter_button.underMouse():
                    self._search_hovered = True
                self._apply_styles()

        elif obj == self.actions_button:
            if event_type == QEvent.Type.Enter:
                self._actions_hovered = True
                self._search_hovered = False
                self._apply_styles()
            elif event_type == QEvent.Type.Leave:
                self._actions_hovered = False
                if self.main_frame.underMouse() and not self.filter_button.underMouse():
                    self._search_hovered = True
                self._apply_styles()

        return super().eventFilter(obj, event)

    def _apply_styles(self) -> None:
        active_surface = self.theme.get_color("bg_tertiary")
        elevated_surface = self.theme.get_color("bg_elevated")
        main_surface = (
            self.theme.get_color("bg_tertiary")
            if self._search_hovered
            else self.theme.get_color("bg_secondary")
        )
        main_border = (
            self.theme.get_color("border_light")
            if (self._search_hovered or self._filter_active)
            else self.theme.get_color("border")
        )
        filter_highlighted_from_search = self._search_hovered
        filter_highlighted_direct = self._filter_hovered or self._filter_active
        actions_highlighted = self._actions_active or self._actions_hovered

        info_style = f"""
        QFrame#searchPanelInfoBox {{
            background-color: {self.theme.get_color('bg_secondary')};
            border: 1px solid {self.theme.get_color('border')};
            border-radius: 8px;
        }}
        QLabel#searchPanelInfoLabel {{
            color: {self.theme.get_color('text_secondary')};
            font-size: 11px;
            font-weight: 600;
            background: transparent;
        }}
        """
        self.info_primary_frame.setStyleSheet(info_style)
        self.info_secondary_frame.setStyleSheet(info_style)

        filter_bg = "transparent"
        filter_radius = "8px"

        if filter_highlighted_direct or filter_highlighted_from_search:
            filter_bg = active_surface

        self.main_frame.setStyleSheet(
            f"""
            QFrame#searchPanelMainFrame {{
                background-color: {main_surface};
                border: 1px solid {main_border};
                border-radius: 8px;
            }}
            QPushButton#searchPanelSearchButton {{
                background: transparent;
                border: none;
                border-radius: 8px;
            }}
            QPushButton#searchPanelSearchButton:hover {{
                background: rgba(255,255,255,0.05);
            }}
            QLineEdit#searchPanelLineEdit {{
                background: transparent;
                border: none;
                color: {self.theme.get_color('text_primary')};
                font-size: 12px;
                padding: 0 8px 0 2px;
            }}
            QPushButton#searchPanelFilterButton {{
                background: {filter_bg};
                border: none;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
                border-top-left-radius: 6px;
                border-bottom-left-radius: 6px;
                margin: 0px 0px 2px 0px;
                padding: 0px;
            }}
            QPushButton#searchPanelFilterButton:hover {{
                background-color: {active_surface};
            }}
            QPushButton#searchPanelFilterButton:pressed {{
                background-color: {elevated_surface};
            }}
            """
        )

        actions_bg = active_surface if actions_highlighted else self.theme.get_color("bg_secondary")

        self.actions_button.setStyleSheet(
            f"""
            QPushButton#searchPanelActionsButton {{
                background-color: {actions_bg};
                border: 1px solid {self.theme.get_color('border')};
                border-radius: 8px;
            }}
            QPushButton#searchPanelActionsButton:hover {{
                background-color: {active_surface};
                border-color: {self.theme.get_color('border_light')};
            }}
            QPushButton#searchPanelActionsButton:pressed {{
                background-color: {elevated_surface};
            }}
            """
        )

        for frame in (self.info_primary_frame, self.info_secondary_frame):
            if hasattr(frame, '_close_btn'):
                frame._close_btn.setStyleSheet(f"""
                    QPushButton#infoCloseBtn {{
                        background: transparent;
                        border: none;
                        border-radius: 10px;
                    }}
                    QPushButton#infoCloseBtn:hover {{
                        background-color: rgba(239, 91, 91, 0.25);
                    }}
                """)

    def set_filter_active(self, active: bool) -> None:
        self._filter_active = active
        self._apply_styles()

    def set_actions_active(self, active: bool) -> None:
        self._actions_active = active
        self._apply_styles()

    def set_info_texts(self, primary: str = "", secondary: str = "") -> None:
        if primary:
            self.info_primary_frame._label.setText(primary)
            self.info_primary_frame.adjustSize()
            self.info_primary_frame.show()
        else:
            self.info_primary_frame.hide()

        if secondary:
            self.info_secondary_frame._label.setText(secondary)
            self.info_secondary_frame.adjustSize()
            self.info_secondary_frame.show()
        else:
            self.info_secondary_frame.hide()

    def set_text(self, text: str) -> None:
        self.search_input.setText(text)

    def text(self) -> str:
        return self.search_input.text().strip()

    def clear(self) -> None:
        self.search_input.clear()

    def line_edit(self) -> QLineEdit:
        return self.search_input

    def filter_anchor(self):
        return self.filter_button

    def actions_anchor(self):
        return self.actions_button

    def show_author_close(self) -> None:
        if hasattr(self.info_primary_frame, '_close_btn'):
            self.info_primary_frame._close_btn.show()

    def hide_author_close(self) -> None:
        if hasattr(self.info_primary_frame, '_close_btn'):
            self.info_primary_frame._close_btn.hide()

    def set_browse_toggle_visible(self, visible: bool) -> None:
        self.browse_toggle.setVisible(visible)
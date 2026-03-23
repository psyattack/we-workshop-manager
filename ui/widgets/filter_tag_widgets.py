from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QFontMetrics
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget


class FilterTagChip(QFrame):
    state_changed = pyqtSignal()

    STATE_NEUTRAL = 0
    STATE_INCLUDED = 1
    STATE_EXCLUDED = 2

    def __init__(self, text: str, theme_manager, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self._text = text
        self._state = self.STATE_NEUTRAL
        self._horizontal_padding = 8
        self._vertical_padding = 2
        self._fixed_height = 20
        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(self._fixed_height)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(
            self._horizontal_padding,
            self._vertical_padding,
            self._horizontal_padding,
            self._vertical_padding,
        )
        layout.setSpacing(0)

        self.label = QLabel(self._text, self)
        self.label.setWordWrap(False)
        self.label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.label)

    def sizeHint(self) -> QSize:
        metrics = QFontMetrics(self.label.font())
        text_width = metrics.horizontalAdvance(self._text)
        width = text_width + self._horizontal_padding * 2 + 2
        return QSize(width, self._fixed_height)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    def state_value(self) -> int:
        return self._state

    def reset(self) -> None:
        self._state = self.STATE_NEUTRAL
        self._apply_style()

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._state == self.STATE_NEUTRAL:
                self._state = self.STATE_INCLUDED
            elif self._state == self.STATE_INCLUDED:
                self._state = self.STATE_NEUTRAL
            elif self._state == self.STATE_EXCLUDED:
                self._state = self.STATE_NEUTRAL
            self._apply_style()
            self.state_changed.emit()
            return

        if event.button() == Qt.MouseButton.RightButton:
            if self._state == self.STATE_NEUTRAL:
                self._state = self.STATE_EXCLUDED
            elif self._state == self.STATE_EXCLUDED:
                self._state = self.STATE_NEUTRAL
            elif self._state == self.STATE_INCLUDED:
                self._state = self.STATE_EXCLUDED
            self._apply_style()
            self.state_changed.emit()
            return

        super().mousePressEvent(event)

    def _apply_style(self) -> None:
        if self._state == self.STATE_INCLUDED:
            bg_color = self.theme.get_color("primary")
            border_color = self.theme.get_color("primary_hover")
            text_color = self.theme.get_color("text_primary")
        elif self._state == self.STATE_EXCLUDED:
            bg_color = self.theme.get_color("accent_red")
            border_color = self.theme.get_color("accent_red_hover")
            text_color = self.theme.get_color("text_primary")
        else:
            bg_color = self.theme.get_color("bg_tertiary")
            border_color = self.theme.get_color("border")
            text_color = self.theme.get_color("text_secondary")

        self.setStyleSheet(
            f"""
            FilterTagChip {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
            """
        )

        self.label.setStyleSheet(
            f"""
            QLabel {{
                color: {text_color};
                font-size: 10px;
                font-weight: 500;
                background: transparent;
                border: none;
            }}
            """
        )

    def text(self) -> str:
        return self._text


class CompactFlowLayout(QVBoxLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._max_width = 280
        self._current_row = None
        self._current_row_width = 0
        self._horizontal_spacing = 5
        self._vertical_spacing = 5
        self.setSpacing(self._vertical_spacing)

    def set_max_width(self, width: int) -> None:
        self._max_width = width

    def add_widget_flow(self, widget: QWidget) -> None:
        hint = widget.sizeHint()
        min_hint = widget.minimumSizeHint()
        widget_width = max(hint.width(), min_hint.width()) + self._horizontal_spacing

        if self._current_row is None or self._current_row_width + widget_width > self._max_width:
            self._start_new_row()

        self._current_row.addWidget(widget)
        self._current_row_width += widget_width

    def finish(self) -> None:
        if self._current_row:
            self._current_row.addStretch()

    def _start_new_row(self) -> None:
        parent_widget = self.parentWidget()
        row_widget = QWidget(parent_widget)
        row_widget.setStyleSheet("background: transparent; border: none;")
        row_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(self._horizontal_spacing)
        row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.addWidget(row_widget)
        self._current_row = row_layout
        self._current_row_width = 0


class FilterTagsFlowWidget(QWidget):
    changed = pyqtSignal()

    def __init__(
        self,
        tags: list[str],
        translated_map: dict[str, str],
        theme_manager,
        max_width: int = 700,
        parent=None,
    ):
        super().__init__(parent)
        self.theme = theme_manager
        self._tags = tags
        self._translated_map = translated_map
        self._chips: dict[str, FilterTagChip] = {}
        self._max_width = max_width
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet("background: transparent; border: none;")

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        flow = CompactFlowLayout()
        flow.set_max_width(self._max_width)

        container = QWidget(self)
        container.setStyleSheet("background: transparent; border: none;")
        container.setLayout(flow)
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        for tag in self._tags:
            chip = FilterTagChip(self._translated_map.get(tag, tag), self.theme, self)
            chip.state_changed.connect(self.changed.emit)
            self._chips[tag] = chip
            flow.add_widget_flow(chip)

        flow.finish()
        self._main_layout.addWidget(container)

    def get_included(self) -> list[str]:
        return [
            tag
            for tag, chip in self._chips.items()
            if chip.state_value() == FilterTagChip.STATE_INCLUDED
        ]

    def get_excluded(self) -> list[str]:
        return [
            tag
            for tag, chip in self._chips.items()
            if chip.state_value() == FilterTagChip.STATE_EXCLUDED
        ]

    def reset_all(self) -> None:
        for chip in self._chips.values():
            chip.reset()
        self.changed.emit()

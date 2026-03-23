from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


GROUP_SPACING = 8
ROW_SPACING = 8
CHIP_SPACING = 4
MAX_ROW_WIDTH = 270
CHIP_HEIGHT = 20


class TagChip(QFrame):
    def __init__(self, text: str, theme_manager, is_key: bool = False, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self._is_key = is_key
        self._setup_ui(text)

    def _setup_ui(self, text: str) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(0)

        label = QLabel(text, self)
        label.setStyleSheet(
            f"""
            color: {self.theme.get_color('text_primary')};
            font-size: 11px;
            font-weight: {'600' if self._is_key else 'normal'};
            background: transparent;
            border: none;
            """
        )
        layout.addWidget(label)

        if self._is_key:
            bg_color = self.theme.get_color("primary")
            border_color = self.theme.get_color("primary_hover")
        else:
            bg_color = self.theme.get_color("bg_tertiary")
            border_color = self.theme.get_color("border")

        self.setStyleSheet(
            f"""
            TagChip {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
            }}
            """
        )
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        self.setFixedHeight(CHIP_HEIGHT)


class TagGroupWidget(QWidget):
    def __init__(
        self,
        key: str,
        values: list[str],
        theme_manager,
        max_width: int = MAX_ROW_WIDTH,
        parent=None,
    ):
        super().__init__(parent)
        self.theme = theme_manager
        self._max_width = max_width
        self._setup_ui(key, values)

    def _create_row(self) -> tuple[QWidget, QHBoxLayout]:
        row_widget = QWidget(self)
        row_widget.setStyleSheet("background: transparent; border: none;")

        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(CHIP_SPACING)
        row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        return row_widget, row_layout

    def _setup_ui(self, key: str, values: list[str]) -> None:
        self.setStyleSheet("background: transparent; border: none;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(ROW_SPACING)

        chips = [TagChip(key, self.theme, is_key=True, parent=self)]
        chips.extend(
            TagChip(value.strip(), self.theme, is_key=False, parent=self)
            for value in values
            if value.strip()
        )

        current_row_widget = None
        current_row_layout = None
        current_row_width = 0

        for chip in chips:
            chip_width = chip.sizeHint().width()

            if current_row_layout is None:
                current_row_widget, current_row_layout = self._create_row()
                main_layout.addWidget(current_row_widget)
                current_row_width = 0

            projected_width = chip_width if current_row_width == 0 else current_row_width + CHIP_SPACING + chip_width

            if projected_width > self._max_width:
                current_row_layout.addStretch()
                current_row_widget, current_row_layout = self._create_row()
                main_layout.addWidget(current_row_widget)
                current_row_width = 0

            current_row_layout.addWidget(chip)

            if current_row_width == 0:
                current_row_width = chip_width
            else:
                current_row_width += CHIP_SPACING + chip_width

        if current_row_layout is not None:
            current_row_layout.addStretch()


class TagsContainer(QWidget):
    def __init__(self, theme_manager, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet("background: transparent; border: none;")

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(GROUP_SPACING)

    def clear(self) -> None:
        while self._main_layout.count():
            item = self._main_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def add_tag_group(self, key: str, values: list[str]) -> None:
        group = TagGroupWidget(
            key=key,
            values=values,
            theme_manager=self.theme,
            max_width=MAX_ROW_WIDTH,
            parent=self,
        )
        self._main_layout.addWidget(group)

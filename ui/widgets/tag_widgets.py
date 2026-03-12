from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout, QWidget


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

        label = QLabel(text)
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
        self.setFixedHeight(20)


class SimpleFlowLayout(QVBoxLayout):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows = []
        self._current_row = None
        self._max_width = 280
        self._current_row_width = 0
        self._horizontal_spacing = 6
        self._vertical_spacing = 6
        self.setSpacing(self._vertical_spacing)

    def set_max_width(self, width: int) -> None:
        self._max_width = width

    def add_widget_flow(self, widget: QWidget) -> None:
        widget_width = widget.sizeHint().width() + self._horizontal_spacing

        if self._current_row is None or self._current_row_width + widget_width > self._max_width:
            self._start_new_row()

        self._current_row.addWidget(widget)
        self._current_row_width += widget_width

    def finish(self) -> None:
        if self._current_row:
            self._current_row.addStretch()

    def _start_new_row(self) -> None:
        row_widget = QWidget()
        row_widget.setStyleSheet("background: transparent; border: none;")

        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(self._horizontal_spacing)
        row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.addWidget(row_widget)
        self._rows.append(row_widget)
        self._current_row = row_layout
        self._current_row_width = 0


class TagGroupWidget(QWidget):
    def __init__(self, key: str, values: list[str], theme_manager, max_width: int = 280, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self._max_width = max_width
        self._setup_ui(key, values)

    def _setup_ui(self, key: str, values: list[str]) -> None:
        self.setStyleSheet("background: transparent; border: none;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(3)

        chips = [TagChip(key, self.theme, is_key=True)]
        for value in values:
            if value.strip():
                chips.append(TagChip(value.strip(), self.theme, is_key=False))

        horizontal_spacing = 4
        current_row_layout = None
        current_row_width = 0

        for chip in chips:
            chip_width = chip.sizeHint().width() + horizontal_spacing

            if current_row_layout is None or current_row_width + chip_width > self._max_width:
                row_widget = QWidget()
                row_widget.setStyleSheet("background: transparent; border: none;")

                current_row_layout = QHBoxLayout(row_widget)
                current_row_layout.setContentsMargins(0, 0, 0, 0)
                current_row_layout.setSpacing(horizontal_spacing)
                current_row_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

                main_layout.addWidget(row_widget)
                current_row_width = 0

            current_row_layout.addWidget(chip)
            current_row_width += chip_width

        if current_row_layout:
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
        self._main_layout.setSpacing(8)

    def clear(self) -> None:
        while self._main_layout.count():
            child = self._main_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()

    def add_tag_group(self, key: str, values: list[str]) -> None:
        group_widget = QWidget()
        group_widget.setStyleSheet("background: transparent; border: none;")

        group_layout = QVBoxLayout(group_widget)
        group_layout.setContentsMargins(0, 0, 0, 0)
        group_layout.setSpacing(6)

        key_chip = TagChip(key, self.theme, is_key=True)

        key_row = QWidget()
        key_row.setStyleSheet("background: transparent; border: none;")

        key_row_layout = QHBoxLayout(key_row)
        key_row_layout.setContentsMargins(0, 0, 0, 0)
        key_row_layout.setSpacing(0)
        key_row_layout.addWidget(key_chip)
        key_row_layout.addStretch()

        group_layout.addWidget(key_row)

        if values:
            flow = SimpleFlowLayout()
            flow.set_max_width(270)

            values_widget = QWidget()
            values_widget.setStyleSheet("background: transparent; border: none;")
            values_widget.setLayout(flow)

            for value in values:
                if value.strip():
                    chip = TagChip(value.strip(), self.theme, is_key=False)
                    flow.add_widget_flow(chip)

            flow.finish()
            group_layout.addWidget(values_widget)

        self._main_layout.addWidget(group_widget)
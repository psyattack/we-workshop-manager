from typing import Optional

from PyQt6.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation, QRect, QSize, Qt, QTimer
from PyQt6.QtWidgets import QHBoxLayout, QLayout, QLayoutItem, QVBoxLayout, QWidget


class FlowLayout(QLayout):
    def __init__(self, parent=None, margin: int = 0, h_spacing: int = 2, v_spacing: int = 2):
        super().__init__(parent)

        self._items: list[QLayoutItem] = []
        self._h_spacing = h_spacing
        self._v_spacing = v_spacing

        self._cached_width = -1
        self._cached_height = -1
        self._cached_item_positions: list[QRect] = []

        self._animate = True
        self._animation_group: Optional[QParallelAnimationGroup] = None

        self._min_item_size = 160
        self._max_item_size = 240
        self._target_item_size = 185
        self._current_item_size = 185
        self._current_columns = 4

        if margin >= 0:
            self.setContentsMargins(margin, margin, margin, margin)

    def set_item_size_range(self, min_size: int, max_size: int, target: int) -> None:
        self._min_item_size = min_size
        self._max_item_size = max_size
        self._target_item_size = target

    def set_animate(self, animate: bool) -> None:
        self._animate = animate

    def get_current_item_size(self) -> int:
        return self._current_item_size

    def get_current_columns(self) -> int:
        return self._current_columns

    def addItem(self, item: QLayoutItem):
        self._items.append(item)
        self._invalidate_cache()

    def count(self) -> int:
        return len(self._items)

    def itemAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self._items):
            return self._items[index]
        return None

    def takeAt(self, index: int) -> Optional[QLayoutItem]:
        if 0 <= index < len(self._items):
            self._invalidate_cache()
            return self._items.pop(index)
        return None

    def clear(self) -> None:
        self._stop_animations()

        while self._items:
            item = self._items.pop()
            if item.widget():
                item.widget().setParent(None)

        self._invalidate_cache()

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self) -> bool:
        return True

    def heightForWidth(self, width: int) -> int:
        return self._do_layout(QRect(0, 0, width, 0), test_only=True)

    def setGeometry(self, rect: QRect):
        super().setGeometry(rect)
        self._do_layout(rect, test_only=False)

    def sizeHint(self) -> QSize:
        return self.minimumSize()

    def minimumSize(self) -> QSize:
        size = QSize()
        for item in self._items:
            size = size.expandedTo(item.minimumSize())

        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def force_update(self) -> None:
        self._invalidate_cache()
        if self.parent():
            self.parent().updateGeometry()
        self.update()
        self.activate()

    def _invalidate_cache(self) -> None:
        self._cached_width = -1
        self._cached_height = -1
        self._cached_item_positions.clear()

    def _stop_animations(self) -> None:
        if self._animation_group is not None:
            self._animation_group.stop()
            self._animation_group.clear()
            self._animation_group = None

    def _calculate_item_size(self, available_width: int) -> tuple[int, int]:
        if available_width <= 0:
            return self._target_item_size, 4

        target_with_spacing = self._target_item_size + self._h_spacing
        columns = max(1, available_width // target_with_spacing)

        total_spacing = (columns - 1) * self._h_spacing
        item_size = (available_width - total_spacing) // columns
        item_size = max(self._min_item_size, min(item_size, self._max_item_size))

        while columns > 1:
            total_spacing = (columns - 1) * self._h_spacing
            required_width = columns * item_size + total_spacing
            if required_width <= available_width:
                break

            columns -= 1
            total_spacing = (columns - 1) * self._h_spacing
            item_size = (available_width - total_spacing) // columns
            item_size = max(self._min_item_size, min(item_size, self._max_item_size))

        return item_size, columns

    def _do_layout(self, rect: QRect, test_only: bool) -> int:
        if not self._items:
            return 0

        margins = self.contentsMargins()
        effective_rect = rect.adjusted(
            margins.left(),
            margins.top(),
            -margins.right(),
            -margins.bottom(),
        )

        available_width = effective_rect.width()
        item_size, columns = self._calculate_item_size(available_width)

        self._current_item_size = item_size
        self._current_columns = columns

        new_positions: list[QRect] = []

        x = effective_rect.x()
        y = effective_rect.y()
        row_height = item_size
        column_index = 0

        for item in self._items:
            widget = item.widget()
            if widget is None:
                continue

            if column_index >= columns:
                column_index = 0
                x = effective_rect.x()
                y += row_height + self._v_spacing

            item_rect = QRect(x, y, item_size, item_size)
            new_positions.append(item_rect)

            x += item_size + self._h_spacing
            column_index += 1

        total_height = y + row_height - effective_rect.y() + margins.bottom()

        if not test_only:
            should_animate = (
                self._animate
                and self._cached_item_positions
                and len(self._cached_item_positions) == len(new_positions)
                and self._cached_width == available_width
            )

            if should_animate:
                self._animate_to_positions(new_positions)
            else:
                self._apply_positions_immediate(new_positions)

            self._cached_width = available_width
            self._cached_height = total_height
            self._cached_item_positions = new_positions

        return total_height

    def _apply_positions_immediate(self, positions: list[QRect]) -> None:
        visible_items = [item for item in self._items if item.widget()]

        for index, item in enumerate(visible_items):
            if index >= len(positions):
                continue

            widget = item.widget()
            if widget is None:
                continue

            rect = positions[index]
            widget.setGeometry(rect)
            self._resize_grid_item(widget, rect.width())

    def _resize_grid_item(self, widget: QWidget, new_size: int) -> None:
        if not hasattr(widget, "item_size"):
            return

        old_size = widget.item_size
        if old_size == new_size:
            return

        widget.item_size = new_size
        widget.setFixedSize(new_size, new_size)

        if hasattr(widget, "overlay_container"):
            widget.overlay_container.setFixedSize(new_size, new_size)

        if hasattr(widget, "preview_label"):
            widget.preview_label.setFixedSize(new_size, new_size)

        if hasattr(widget, "_movie") and widget._movie:
            widget._movie.setScaledSize(QSize(new_size, new_size))
        elif hasattr(widget, "_pixmap") and widget._pixmap and not widget._pixmap.isNull():
            if hasattr(widget, "_apply_pixmap"):
                widget._apply_pixmap(new_size)

        if hasattr(widget, "name_container"):
            name_height = max(24, int(new_size * 0.22))
            widget.name_container.setFixedHeight(name_height)
            widget.name_container.setFixedWidth(new_size)
            widget.name_container.move(0, new_size - name_height)

        if hasattr(widget, "name_label"):
            font_size = max(6, min(12, int(new_size / 12)))
            widget.name_label.setStyleSheet(
                f"""
                color: white;
                font-size: {font_size}px;
                font-weight: bold;
                background: transparent;
                """
            )
            widget.name_label.setMaximumWidth(new_size - 10)

            if hasattr(widget, "_original_title") and hasattr(widget, "_set_elided_text"):
                widget._set_elided_text(widget._original_title)

        if hasattr(widget, "status_indicator"):
            widget.status_indicator.move(new_size - 33, 4)

        if hasattr(widget, "download_overlay"):
            widget.download_overlay.setFixedSize(new_size, new_size)
            widget.download_overlay._size = new_size

        if hasattr(widget, "circular_progress"):
            circle_size = max(50, int(new_size * 0.38))
            cx = (new_size - circle_size) // 2
            cy = (new_size - circle_size) // 2
            widget.circular_progress.move(cx, cy)

    def _animate_to_positions(self, new_positions: list[QRect]) -> None:
        self._stop_animations()
        self._animation_group = QParallelAnimationGroup()

        visible_items = [item for item in self._items if item.widget()]

        for index, item in enumerate(visible_items):
            if index >= len(new_positions) or index >= len(self._cached_item_positions):
                continue

            widget = item.widget()
            if widget is None:
                continue

            old_rect = self._cached_item_positions[index]
            new_rect = new_positions[index]

            if old_rect.size() != new_rect.size():
                self._resize_grid_item(widget, new_rect.width())

            if old_rect.topLeft() != new_rect.topLeft():
                animation = QPropertyAnimation(widget, b"pos")
                animation.setDuration(200)
                animation.setStartValue(old_rect.topLeft())
                animation.setEndValue(new_rect.topLeft())
                animation.setEasingCurve(QEasingCurve.Type.OutCubic)
                self._animation_group.addAnimation(animation)
            else:
                widget.move(new_rect.topLeft())

        if self._animation_group.animationCount() > 0:
            self._animation_group.start()
        else:
            self._animation_group = None


class AdaptiveGridWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._flow_layout = FlowLayout(self, margin=0, h_spacing=2, v_spacing=2)
        self._items: list[QWidget] = []

        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(True)
        self._update_timer.timeout.connect(self._delayed_update)

    def get_layout(self) -> FlowLayout:
        return self._flow_layout

    def add_item(self, widget: QWidget) -> None:
        self._items.append(widget)
        self._flow_layout.addWidget(widget)

    def clear_items(self) -> None:
        self._flow_layout.clear()
        self._items.clear()

    def get_items(self) -> list[QWidget]:
        return self._items.copy()

    def get_current_item_size(self) -> int:
        return self._flow_layout.get_current_item_size()

    def get_current_columns(self) -> int:
        return self._flow_layout.get_current_columns()

    def set_item_size_range(self, min_size: int, max_size: int, target: int) -> None:
        self._flow_layout.set_item_size_range(min_size, max_size, target)

    def set_animate(self, animate: bool) -> None:
        self._flow_layout.set_animate(animate)

    def update_layout(self) -> None:
        self._flow_layout.force_update()

    def schedule_layout_update(self, delay_ms: int = 50) -> None:
        self._update_timer.start(delay_ms)

    def _delayed_update(self) -> None:
        self._flow_layout.force_update()
        self.updateGeometry()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(10, self._delayed_update)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._flow_layout.force_update()
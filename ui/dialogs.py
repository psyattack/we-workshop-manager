from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QFrame, QGraphicsDropShadowEffect, QWidget,
    QComboBox, QLineEdit, QScrollArea, QTabWidget, QCheckBox
)
from PyQt6.QtCore import Qt, QSize, QPoint, QTimer, QEvent, pyqtSignal, QPropertyAnimation, QEasingCurve, QRectF, pyqtProperty
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen
from core.resources import get_icon, get_pixmap
from core.constants import APP_FULL_NAME
from ui.notifications import MessageBox
from ui.grid_items import SmallCircularProgress
from utils.helpers import hex_to_rgba
import re
import webbrowser
from utils.helpers import restart_application
from ui.workshop_tab import PreviewPopup


class AnimatedToggle(QWidget):
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None, theme_manager=None):
        super().__init__(parent)
        self.theme = theme_manager
        self._checked = False
        self._circle_position = 3.0
        self._background_color = QColor(self._get_color('bg_tertiary'))
        
        self.setFixedSize(44, 24)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        self._position_animation = QPropertyAnimation(self, b"circle_position")
        self._position_animation.setDuration(200)
        self._position_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        self._color_animation = QPropertyAnimation(self, b"background_color")
        self._color_animation.setDuration(200)
        self._color_animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
    
    def _get_color(self, color_name: str) -> str:
        if self.theme:
            return self.theme.get_color(color_name)
        colors = {
            'bg_tertiary': '#252938',
            'primary': '#4A7FD9',
            'border': '#2A2F42',
        }
        return colors.get(color_name, '#FFFFFF')
    
    def get_circle_position(self) -> float:
        return self._circle_position
    
    def set_circle_position(self, pos: float):
        self._circle_position = pos
        self.update()
    
    circle_position = pyqtProperty(float, get_circle_position, set_circle_position)
    
    def get_background_color(self) -> QColor:
        return self._background_color
    
    def set_background_color(self, color: QColor):
        self._background_color = color
        self.update()
    
    background_color = pyqtProperty(QColor, get_background_color, set_background_color)
    
    def isChecked(self) -> bool:
        return self._checked
    
    def setChecked(self, checked: bool):
        if self._checked == checked:
            return
        self._checked = checked
        self._animate()
    
    def toggle(self):
        self._checked = not self._checked
        self._animate()
        self.toggled.emit(self._checked)
    
    def _animate(self):
        self._position_animation.stop()
        self._color_animation.stop()
        
        if self._checked:
            self._position_animation.setStartValue(self._circle_position)
            self._position_animation.setEndValue(self.width() - 21.0)
            self._color_animation.setStartValue(self._background_color)
            self._color_animation.setEndValue(QColor(self._get_color('primary')))
        else:
            self._position_animation.setStartValue(self._circle_position)
            self._position_animation.setEndValue(3.0)
            self._color_animation.setStartValue(self._background_color)
            self._color_animation.setEndValue(QColor(self._get_color('bg_tertiary')))
        
        self._position_animation.start()
        self._color_animation.start()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        painter.setPen(QPen(QColor(self._get_color('border')), 1))
        painter.setBrush(QBrush(self._background_color))
        painter.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 12, 12)
        
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        circle_y = (self.height() - 18) / 2
        painter.drawEllipse(QRectF(self._circle_position, circle_y, 18, 18))


class CustomDialog(QDialog):
    def __init__(self, title: str = "Dialog", parent=None, theme_manager=None):
        super().__init__(parent)

        self.theme = theme_manager
        self._setup_colors()

        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.container = QFrame(self)
        self._apply_container_style()

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.addWidget(self.container)

        self.content_layout = QVBoxLayout(self.container)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(15)

        self._create_title_bar(title)

        self.old_pos = None

    def _setup_colors(self):
        if self.theme:
            self.c_bg_primary = self.theme.get_color('bg_primary')
            self.c_bg_secondary = self.theme.get_color('bg_secondary')
            self.c_bg_tertiary = self.theme.get_color('bg_tertiary')
            self.c_border = self.theme.get_color('border')
            self.c_border_light = self.theme.get_color('border_light')
            self.c_text_primary = self.theme.get_color('text_primary')
            self.c_text_secondary = self.theme.get_color('text_secondary')
            self.c_text_disabled = self.theme.get_color('text_disabled')
            self.c_primary = self.theme.get_color('primary')
            self.c_primary_hover = self.theme.get_color('primary_hover')
            self.c_accent_red = self.theme.get_color('accent_red')
            self.c_overlay = self.theme.get_color('overlay')
        else:
            self.c_bg_primary = '#0F111A'
            self.c_bg_secondary = '#1A1D2E'
            self.c_bg_tertiary = '#252938'
            self.c_border = '#2A2F42'
            self.c_border_light = '#3A3F52'
            self.c_text_primary = '#FFFFFF'
            self.c_text_secondary = '#B4B7C3'
            self.c_text_disabled = '#6B6E7C'
            self.c_primary = '#4A7FD9'
            self.c_primary_hover = '#5B8FE9'
            self.c_accent_red = '#EF5B5B'
            self.c_overlay = 'rgba(0, 0, 0, 0.4)'

    def _apply_container_style(self):
        bg_rgba = hex_to_rgba(self.c_bg_secondary, 240)
        self.container.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_rgba};
                border-radius: 12px;
                border: 2px solid {self.c_border_light};
            }}
        """)

    def _create_title_bar(self, title):
        title_bar = QWidget()
        title_bar.setFixedHeight(40)
        title_bar.setStyleSheet("QWidget { background: transparent; border: none; }")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(0, 0, 0, 10)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 700;
            color: {self.c_text_primary};
            background: transparent;
        """)

        close_btn = QPushButton()
        close_btn.setFixedSize(32, 32)
        close_btn.setIcon(get_icon("ICON_CLOSE"))
        close_btn.setIconSize(QSize(20, 20))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                border-radius: 16px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: rgba(239, 91, 91, 0.2);
            }
            QPushButton:pressed {
                background-color: rgba(239, 91, 91, 0.3);
            }
        """)
        close_btn.clicked.connect(self.reject)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(close_btn)
        self.content_layout.addWidget(title_bar)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.old_pos and event.buttons() == Qt.MouseButton.LeftButton:
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.pos() + delta)
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.old_pos = None


class DownloadsDialog(CustomDialog):
    download_cancelled = pyqtSignal(str)

    def __init__(self, translator, theme_manager, download_manager, parser, parent=None):
        super().__init__(translator.t("dialog.tasks"), parent, theme_manager)

        self.tr = translator
        self.dm = download_manager
        self.parser = parser
        self._preview_url_cache = {}
        self._file_size_cache = {}

        self.setFixedSize(400, 400)

        self._setup_content()
        self._setup_preview_popup()
        self._setup_update_timer()

    def _setup_content(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: {self.c_bg_tertiary};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.c_border_light};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.c_primary};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        self.scroll_container = QWidget()
        self.scroll_container.setStyleSheet("background: transparent;")
        self.scroll_layout = QVBoxLayout(self.scroll_container)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_layout.setSpacing(6)
        scroll.setWidget(self.scroll_container)

        self.content_layout.addWidget(scroll)

    def _setup_preview_popup(self):
        self.preview_popup = PreviewPopup(self.theme, self.tr, self)

    def _setup_update_timer(self):
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_list)
        self.update_timer.setInterval(500)

    def showEvent(self, event):
        super().showEvent(event)
        self.update_timer.start()
        self._update_list()

    def hideEvent(self, event):
        self.update_timer.stop()
        self.preview_popup.hide_preview()
        self.preview_popup.force_cancel()
        super().hideEvent(event)

    def set_caches(self, preview_cache: dict, size_cache: dict):
        self._preview_url_cache = preview_cache
        self._file_size_cache = size_cache

    def showAt(self, global_pos: QPoint):
        self.move(global_pos)
        self.show()

    def _update_list(self):
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child is not None and child.widget() is not None:
                try:
                    child.widget().deleteLater()
                except RuntimeError:
                    pass

        all_tasks = []
        for pubfileid, info in self.dm.downloading.items():
            all_tasks.append(("download", pubfileid, info))
        for pubfileid, info in self.dm.extracting.items():
            all_tasks.append(("extract", pubfileid, info))

        if not all_tasks:
            label = QLabel(self.tr.t("labels.no_tasks"))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"""
                color: {self.c_text_secondary};
                font-size: 13px;
                background-color: {self.c_bg_tertiary};
                padding: 12px 16px;
                border-radius: 8px;
            """)
            label.setFixedHeight(60)
            self.scroll_layout.addWidget(label)
        else:
            for task_type, pubfileid, info in all_tasks:
                self._create_task_item(task_type, pubfileid, info)

        self.scroll_layout.addStretch()

    def _create_task_item(self, task_type: str, pubfileid: str, info: dict):
        item_widget = QWidget()
        item_widget.setFixedHeight(68)
        item_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {self.c_bg_tertiary};
                border: 2px solid {self.c_border_light};
                border-radius: 8px;
            }}
        """)

        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(8, 8, 10, 8)
        item_layout.setSpacing(10)

        mini_progress = SmallCircularProgress(
            size=52, line_width=3, theme_manager=self.theme, parent=item_widget
        )
        mini_progress.setStyleSheet("border: none;")
        status_text = info.get("status", "")
        file_size_bytes = self._file_size_cache.get(pubfileid, 0)
        is_extraction = (task_type == "extract")
        mini_progress.update_from_status(status_text, file_size_bytes, is_extraction)
        item_layout.addWidget(mini_progress)

        text_container = QWidget()
        text_container.setStyleSheet("background: transparent; border: none;")
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        short_id = pubfileid[:12] + "..." if len(pubfileid) > 12 else pubfileid
        if task_type == "download":
            prefix = self.tr.t("labels.download_prefix", id=short_id)
        else:
            prefix = self.tr.t("labels.extract_prefix", id=short_id)

        title_label = QLabel(prefix)
        title_label.setStyleSheet(f"""
            color: {self.c_text_primary};
            font-size: 12px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)
        title_label.setCursor(Qt.CursorShape.PointingHandCursor)
        title_label.setProperty("pubfileid", pubfileid)
        title_label.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        title_label.installEventFilter(self)
        title_label.mousePressEvent = lambda e, pid=pubfileid: self._on_open_browser(pid)
        text_layout.addWidget(title_label)

        display_status = status_text[:40] + "..." if len(status_text) > 40 else status_text
        if not display_status:
            display_status = self.tr.t("labels.starting")
        status_label = QLabel(display_status)
        status_label.setStyleSheet(f"""
            color: {self.c_text_disabled};
            font-size: 10px;
            background: transparent;
            border: none;
        """)
        text_layout.addWidget(status_label)

        item_layout.addWidget(text_container, 1)

        if task_type == "download":
            delete_btn = QPushButton()
            delete_btn.setIcon(get_icon("ICON_DELETE"))
            delete_btn.setIconSize(QSize(28, 28))
            delete_btn.setFixedSize(36, 36)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                }
            """)
            delete_btn.clicked.connect(
                lambda checked, pid=pubfileid: self._cancel_download(pid)
            )
            item_layout.addWidget(delete_btn)

        self.scroll_layout.addWidget(item_widget)

    def eventFilter(self, obj, event):
        if isinstance(obj, QLabel):
            pubfileid = obj.property("pubfileid")
            if pubfileid:
                if event.type() == QEvent.Type.Enter:
                    self._show_item_preview(pubfileid, obj)
                    return False
                elif event.type() == QEvent.Type.Leave:
                    self.preview_popup.hide_preview()
                    return False
        return super().eventFilter(obj, event)

    def _show_item_preview(self, pubfileid: str, widget: QWidget):
        preview_url = self._preview_url_cache.get(pubfileid)
        if not preview_url and self.parser:
            cached_item = self.parser.get_cached_item(pubfileid)
            if cached_item and cached_item.preview_url:
                preview_url = cached_item.preview_url
                self._preview_url_cache[pubfileid] = preview_url
        global_pos = widget.mapToGlobal(QPoint(-65, widget.height() // 2 + 12))
        self.preview_popup.show_preview(preview_url or "", global_pos)

    def _on_open_browser(self, pubfileid: str):
        webbrowser.open(
            f"https://steamcommunity.com/sharedfiles/filedetails/?id={pubfileid}"
        )

    def _cancel_download(self, pubfileid: str):
        self.download_cancelled.emit(pubfileid)
        QTimer.singleShot(100, self._update_list)


class BatchDownloadDialog(CustomDialog):
    def __init__(self, translator, parent=None, theme_manager=None):
        super().__init__(translator.t("dialog.batch_download"), parent, theme_manager)

        self.tr = translator
        self.pubfileids = []

        self.setFixedSize(450, 350)

        label = QLabel(self.tr.t("messages.batch_input_placeholder"))
        label.setStyleSheet(f"color: {self.c_text_primary}; background: transparent;")
        label.setWordWrap(True)
        self.content_layout.addWidget(label)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(self.tr.t("labels.id_url_placeholder"))
        self.text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {self.c_bg_tertiary};
                color: {self.c_text_primary};
                border: 2px solid {self.c_border};
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
            }}
            QTextEdit:focus {{
                border-color: {self.c_primary};
            }}
        """)
        self.content_layout.addWidget(self.text_edit)

        btn_layout = QHBoxLayout()

        download_btn = QPushButton(self.tr.t("buttons.download_all"))
        download_btn.setFixedHeight(40)
        download_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.c_primary};
                color: {self.c_text_primary};
                border: none;
                border-radius: 8px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {self.c_primary_hover};
            }}
        """)
        download_btn.clicked.connect(self._on_download)

        btn_layout.addWidget(download_btn)

        self.content_layout.addLayout(btn_layout)

    def _on_download(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            return

        tokens = re.split(r'\s+', text.replace('\n', ' ').replace('\r', ' '))

        seen = set()
        valid_ids = []

        for token in tokens:
            token = token.strip()
            if not token:
                continue

            pubfileid = None

            if token.isdigit() and len(token) >= 8:
                pubfileid = token
            else:
                match = re.search(r'[?&]id=(\d{8,})', token)
                if match:
                    pubfileid = match.group(1)

            if pubfileid and pubfileid not in seen:
                valid_ids.append(pubfileid)
                seen.add(pubfileid)

        self.pubfileids = valid_ids

        if valid_ids:
            self.accept()
        else:
            self._show_warning(self.tr.t("dialog.warning"), self.tr.t("messages.invalid_input"))

    def _show_warning(self, title, message):
        msg_box = MessageBox(self.theme, title, message, MessageBox.Icon.Warning, self)
        msg_box.exec()

    def get_pubfileids(self):
        return self.pubfileids


class InfoDialog(CustomDialog):
    def __init__(self, translator, parent=None, theme_manager=None):
        super().__init__(translator.t("dialog.about"), parent, theme_manager)

        self.tr = translator
        self.setMinimumSize(400, 280)
        self.adjustSize()

        icon = QLabel()
        icon.setPixmap(get_pixmap("ICON_APP", size=100))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("""
            border: none;
            margin-bottom: -10px;
            margin-top: -10px;
        """)
        self.content_layout.addWidget(icon)

        info_text = QLabel(
            f"{APP_FULL_NAME}\n\n"
            f"{self.tr.t('info.description')}\n\n"
            f"{self.tr.t('info.developed')}"
        )
        info_text.setStyleSheet(f"""
            color: {self.c_text_primary};
            font-size: 13px;
            background: transparent;
        """)
        info_text.setWordWrap(True)
        info_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(info_text)

        github_container = QHBoxLayout()
        github_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        github_container.setSpacing(8)

        github_icon = QLabel()
        github_icon.setPixmap(get_pixmap("ICON_GITHUB", size=34))
        github_icon.setStyleSheet("border: none; margin-right: -5px;")

        github_link = QLabel(
            f'<a href="https://github.com/psyattack/we-workshop-manager" style="color: {self.c_primary}; text-decoration: none;">GitHub</a>')
        github_link.setOpenExternalLinks(True)
        github_link.setStyleSheet("border: none; font-size: 14px; font-weight: bold;")

        github_container.addWidget(github_icon)
        github_container.addWidget(github_link)

        self.content_layout.addLayout(github_container)

        ok_btn = QPushButton(self.tr.t("buttons.ok"))
        ok_btn.setFixedHeight(40)
        ok_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.c_primary};
                color: {self.c_text_primary};
                border: none;
                border-radius: 8px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {self.c_primary_hover};
            }}
        """)
        ok_btn.clicked.connect(self.accept)
        self.content_layout.addWidget(ok_btn)


class CollapsibleSection(QWidget):
    def __init__(self, title: str, parent=None, expanded: bool = True, theme_manager=None):
        super().__init__(parent)

        self.theme = theme_manager
        self._setup_colors()

        self._is_expanded = expanded
        self._title_text = title

        self.setStyleSheet("background: transparent; border: none;")

        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        self._header = QPushButton()
        self._header.setCheckable(True)
        self._header.setChecked(expanded)
        self._header.clicked.connect(self._on_toggle)
        self._header.setFixedHeight(38)
        self._update_header_text()
        self._apply_header_style()
        self._main_layout.addWidget(self._header)

        self._content_area = QWidget()
        self._apply_content_style()
        self._content_layout = QVBoxLayout(self._content_area)
        self._content_layout.setContentsMargins(14, 12, 14, 12)
        self._content_layout.setSpacing(10)

        self._main_layout.addWidget(self._content_area)

        self._content_area.setVisible(expanded)

    def _setup_colors(self):
        if self.theme:
            self.c_bg_secondary = self.theme.get_color('bg_secondary')
            self.c_bg_tertiary = self.theme.get_color('bg_tertiary')
            self.c_border = self.theme.get_color('border')
            self.c_border_light = self.theme.get_color('border_light')
            self.c_text_primary = self.theme.get_color('text_primary')
            self.c_text_secondary = self.theme.get_color('text_secondary')
            self.c_primary = self.theme.get_color('primary')
        else:
            self.c_bg_secondary = '#1A1D2E'
            self.c_bg_tertiary = '#252938'
            self.c_border = '#2A2F42'
            self.c_border_light = '#3A3F52'
            self.c_text_primary = '#FFFFFF'
            self.c_text_secondary = '#B4B7C3'
            self.c_primary = '#4A7FD9'

    def _apply_header_style(self):
        self._header.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.c_bg_tertiary};
                color: {self.c_text_secondary};
                border: 1px solid {self.c_border_light};
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 13px;
                font-weight: 700;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {self.c_bg_secondary};
                border-color: {self.c_primary};
                color: {self.c_text_primary};
            }}
            QPushButton:checked {{
                background-color: {self.c_bg_secondary};
                color: {self.c_text_primary};
                border-color: {self.c_primary};
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
        """)

    def _apply_content_style(self):
        self._content_area.setStyleSheet(f"""
            QWidget {{
                background-color: {self.c_bg_secondary};
                border: 1px solid {self.c_border_light};
                border-top: none;
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
            }}
        """)

    def _update_header_text(self):
        arrow = "▼" if self._is_expanded else "▶"
        self._header.setText(f"  {arrow}  {self._title_text}")

    def _on_toggle(self, checked):
        self._is_expanded = checked
        self._update_header_text()
        self._content_area.setVisible(checked)

    def content_layout(self) -> QVBoxLayout:
        return self._content_layout

    def add_widget(self, widget):
        self._content_layout.addWidget(widget)

    def add_layout(self, layout):
        self._content_layout.addLayout(layout)

    def set_expanded(self, expanded: bool):
        self._is_expanded = expanded
        self._header.setChecked(expanded)
        self._update_header_text()
        self._content_area.setVisible(expanded)


class SettingsField(QWidget):
    def __init__(self, label_text: str, control_widget: QWidget, description: str = None,
                 stacked: bool = False, parent=None, theme_manager=None):
        super().__init__(parent)

        self.theme = theme_manager
        self._setup_colors()

        self.setStyleSheet("background: transparent; border: none;")

        if stacked:
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(4)

            if label_text:
                label = QLabel(label_text)
                label.setStyleSheet(f"""
                    font-size: 12px;
                    font-weight: 600;
                    color: {self.c_text_secondary};
                    background: transparent;
                    border: none;
                """)
                layout.addWidget(label)

            if description:
                desc = QLabel(description)
                desc.setWordWrap(True)
                desc.setStyleSheet(f"""
                    font-size: 11px;
                    color: {self.c_text_disabled};
                    background: transparent;
                    border: none;
                    margin-bottom: 2px;
                """)
                layout.addWidget(desc)

            layout.addWidget(control_widget)
        else:
            layout = QHBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(12)

            left = QVBoxLayout()
            left.setSpacing(2)

            if label_text:
                label = QLabel(label_text)
                label.setStyleSheet(f"""
                    font-size: 12px;
                    font-weight: 600;
                    color: {self.c_text_secondary};
                    background: transparent;
                    border: none;
                """)
                left.addWidget(label)

            if description:
                desc = QLabel(description)
                desc.setWordWrap(True)
                desc.setStyleSheet(f"""
                    font-size: 11px;
                    color: {self.c_text_disabled};
                    background: transparent;
                    border: none;
                """)
                left.addWidget(desc)

            layout.addLayout(left, 1)
            
            if isinstance(control_widget, AnimatedToggle):
                layout.addWidget(control_widget, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            elif isinstance(control_widget, QComboBox):
                control_widget.setFixedWidth(140)
                control_widget.setFixedHeight(32)
                layout.addWidget(control_widget, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            else:
                control_widget.setFixedWidth(160)
                layout.addWidget(control_widget, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def _setup_colors(self):
        if self.theme:
            self.c_text_secondary = self.theme.get_color('text_secondary')
            self.c_text_disabled = self.theme.get_color('text_disabled')
        else:
            self.c_text_secondary = '#B4B7C3'
            self.c_text_disabled = '#6B6E7C'


class SettingsPopup(CustomDialog):
    def __init__(self, config, accounts, translator, theme_manager, main_window, parent=None):
        super().__init__(translator.t("settings.title"), parent, theme_manager)

        self.config = config
        self.accounts = accounts
        self.tr = translator
        self.main_window = main_window

        self.setFixedSize(900, 650)

        self._apply_container_style()
        self._setup_ui()

    def _setup_ui(self):
        self.content_layout.setSpacing(10)

        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(self._tab_widget_style())
        self.content_layout.addWidget(self.tab_widget)

        self._create_general_tab()
        self._create_account_tab()
        self._create_advanced_tab()

    def _create_general_tab(self):
        tab = self._create_scrollable_tab()
        layout = tab._inner_layout

        appearance_section = CollapsibleSection(
            self.tr.t("settings.appearance") if self.tr.t("settings.appearance") != "settings.appearance" else "Appearance",
            expanded=True,
            theme_manager=self.theme
        )

        theme_combo = self._create_theme_combo()
        appearance_section.add_widget(SettingsField(
            self.tr.t("settings.theme_dev"),
            theme_combo,
            description=self.tr.t("settings.theme_description") if self.tr.t("settings.theme_description") != "settings.theme_description" else "Select the visual theme for the application",
            theme_manager=self.theme
        ))

        lang_combo = self._create_language_combo()
        appearance_section.add_widget(SettingsField(
            self.tr.t("settings.language"),
            lang_combo,
            description=self.tr.t("settings.language_description") if self.tr.t("settings.language_description") != "settings.language_description" else "Change interface language (requires restart)",
            theme_manager=self.theme
        ))

        show_id_toggle = self._create_show_id_toggle()
        appearance_section.add_widget(SettingsField(
            self.tr.t("settings.show_id_section") if self.tr.t("settings.show_id_section") != "settings.show_id_section" else "Show ID Section",
            show_id_toggle,
            description=self.tr.t("settings.show_id_description") if self.tr.t("settings.show_id_description") != "settings.show_id_description" else "Show or hide the ID section in details panel",
            theme_manager=self.theme
        ))

        layout.addWidget(appearance_section)

        behavior_section = CollapsibleSection(
            self.tr.t("settings.behavior") if self.tr.t("settings.behavior") != "settings.behavior" else "Behavior",
            expanded=True,
            theme_manager=self.theme
        )

        minimize_toggle = self._create_minimize_toggle()
        behavior_section.add_widget(SettingsField(
            self.tr.t("labels.minimize_on_apply"),
            minimize_toggle,
            description=self.tr.t("settings.minimize_description") if self.tr.t("settings.minimize_description") != "settings.minimize_description" else "Minimize window after applying changes",
            theme_manager=self.theme
        ))

        preload_toggle = self._create_preload_toggle()
        behavior_section.add_widget(SettingsField(
            self.tr.t("settings.preload_next_page") if self.tr.t("settings.preload_next_page") != "settings.preload_next_page" else "Preload Next Page",
            preload_toggle,
            description=self.tr.t("settings.preload_description") if self.tr.t("settings.preload_description") != "settings.preload_description" else "Preload the next workshop page in background for faster navigation",
            theme_manager=self.theme
        ))

        layout.addWidget(behavior_section)

        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr.t("settings.tab_general") if self.tr.t("settings.tab_general") != "settings.tab_general" else "General")

    def _create_show_id_toggle(self):
        toggle = AnimatedToggle(theme_manager=self.theme)
        toggle.setChecked(self.config.get_show_id_section())
        toggle.toggled.connect(self._on_show_id_changed)
        return toggle

    def _on_show_id_changed(self, checked: bool):
        self.config.set_show_id_section(checked)
        if self.main_window:
            if hasattr(self.main_window, 'wallpapers_tab') and hasattr(self.main_window.wallpapers_tab, 'details_panel'):
                self.main_window.wallpapers_tab.details_panel._update_id_section_visibility()
            if hasattr(self.main_window, 'workshop_tab') and hasattr(self.main_window.workshop_tab, 'details_panel'):
                self.main_window.workshop_tab.details_panel._update_id_section_visibility()

    def _create_preload_toggle(self):
        toggle = AnimatedToggle(theme_manager=self.theme)
        toggle.setChecked(self.config.get_preload_next_page())
        toggle.toggled.connect(self._on_preload_changed)
        return toggle

    def _on_preload_changed(self, checked: bool):
        self.config.set_preload_next_page(checked)

    def _create_minimize_toggle(self):
        toggle = AnimatedToggle(theme_manager=self.theme)
        toggle.setChecked(self.config.get_minimize_on_apply())
        toggle.toggled.connect(self._on_minimize_changed)
        return toggle

    def _on_minimize_changed(self, checked: bool):
        self.config.set_minimize_on_apply(checked)

    def _create_debug_toggle(self):
        toggle = AnimatedToggle(theme_manager=self.theme)
        toggle.setChecked(self.config.get_debug_mode())
        toggle.toggled.connect(self._on_debug_mode_changed)
        return toggle

    def _on_debug_mode_changed(self, checked: bool):
        current_value = self.config.get_debug_mode()
        if checked == current_value:
            return
        
        self.config.set_debug_mode(checked)
        
        msg_box = MessageBox(
            self.theme,
            self.tr.t("messages.restart_title"),
            self.tr.t("messages.restart_debug_message"),
            MessageBox.Icon.Question,
            self
        )
        yes_btn = msg_box.addButton(self.tr.t("buttons.yes"), MessageBox.ButtonRole.YesRole)
        no_btn = msg_box.addButton(self.tr.t("buttons.no"), MessageBox.ButtonRole.NoRole)
        msg_box.exec()

        if msg_box.clickedButton() == yes_btn:
            restart_application()

    def _create_account_tab(self):
        tab = self._create_scrollable_tab()
        layout = tab._inner_layout

        account_section = CollapsibleSection(
            self.tr.t("settings.account_selection") if self.tr.t("settings.account_selection") != "settings.account_selection" else "Account Selection",
            expanded=True,
            theme_manager=self.theme
        )

        account_combo = self._create_account_combo()
        account_section.add_widget(SettingsField(
            self.tr.t("settings.account"),
            account_combo,
            description=self.tr.t("settings.account_description") if self.tr.t("settings.account_description") != "settings.account_description" else "Select the active Steam account",
            theme_manager=self.theme
        ))

        layout.addWidget(account_section)

        login_section = CollapsibleSection(self.tr.t("settings.steam_login"), expanded=True, theme_manager=self.theme)
        login_widget = self._create_steam_login_section()
        login_section.add_widget(login_widget)

        layout.addWidget(login_section)

        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr.t("settings.tab_account") if self.tr.t("settings.tab_account") != "settings.tab_account" else "Account")

    def _create_advanced_tab(self):
        tab = self._create_scrollable_tab()
        layout = tab._inner_layout

        debug_section = CollapsibleSection(
            self.tr.t("settings.debug") if self.tr.t("settings.debug") != "settings.debug" else "Debug",
            expanded=True,
            theme_manager=self.theme
        )

        debug_toggle = self._create_debug_toggle()
        debug_description = self.tr.t("settings.debug_description") if self.tr.t("settings.debug_description") != "settings.debug_description" else "Enable debug mode for webview testing"
        debug_section.add_widget(SettingsField(
            self.tr.t("settings.debug_mode"),
            debug_toggle,
            description=debug_description,
            theme_manager=self.theme
        ))

        layout.addWidget(debug_section)

        layout.addStretch()
        self.tab_widget.addTab(tab, self.tr.t("settings.tab_advanced") if self.tr.t("settings.tab_advanced") != "settings.tab_advanced" else "Advanced")

    def _create_scrollable_tab(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
            QScrollBar:vertical {{
                background: {self.c_bg_secondary};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {self.c_border_light};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {self.c_primary};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)

        inner = QWidget()
        inner.setStyleSheet("background: transparent;")
        inner_layout = QVBoxLayout(inner)
        inner_layout.setContentsMargins(4, 8, 4, 8)
        inner_layout.setSpacing(12)

        scroll.setWidget(inner)

        scroll._inner_layout = inner_layout
        return scroll

    def _create_account_combo(self):
        combo = QComboBox()
        last_loggin_acc = 1
        for i in range(len(self.accounts.get_accounts()) - last_loggin_acc):
            combo.addItem(f"{self.tr.t('labels.account')} {i + 1}")
        combo.setCurrentIndex(self.config.get_account_number())
        combo.currentIndexChanged.connect(lambda idx: self.config.set_account_number(idx))
        combo.setStyleSheet(self._combo_style())
        return combo

    def _create_theme_combo(self):
        combo = QComboBox()

        self._theme_keys = list(self.theme.THEMES.keys())

        display_names = []
        for key in self._theme_keys:
            tr_key = f"labels.theme_{key}"
            translated = self.tr.t(tr_key)
            if translated == tr_key:
                translated = key.capitalize()
            display_names.append(translated)

        combo.addItems(display_names)

        current = self.config.get_theme()
        if current in self._theme_keys:
            combo.setCurrentIndex(self._theme_keys.index(current))
        else:
            combo.setCurrentIndex(0)

        combo.currentIndexChanged.connect(self._on_theme_changed)
        combo.setStyleSheet(self._combo_style())
        return combo

    def _create_language_combo(self):
        combo = QComboBox()
        languages = list(self.tr.SUPPORTED_LANGUAGES.values())
        combo.addItems(languages)
        
        current_lang = self.config.get_language()
        lang_codes = list(self.tr.SUPPORTED_LANGUAGES.keys())
        current_index = lang_codes.index(current_lang) if current_lang in lang_codes else 0
        combo.setCurrentIndex(current_index)
        combo.currentIndexChanged.connect(self._on_language_changed)
        combo.setStyleSheet(self._combo_style())
        return combo

    def _create_steam_login_section(self):
        container = QWidget()
        container.setStyleSheet("background: transparent; border: none;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        desc = QLabel(self.tr.t("settings.login_description") if self.tr.t("settings.login_description") != "settings.login_description" else "Enter your Steam credentials to authenticate")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"""
            font-size: 11px;
            color: {self.theme.get_color('text_disabled') if self.theme else '#6B6E7C'};
            background: transparent;
            border: none;
            margin-bottom: 4px;
        """)
        layout.addWidget(desc)

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText(self.tr.t("settings.login_placeholder"))
        self.login_input.setStyleSheet(self._input_style())
        layout.addWidget(self.login_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(self.tr.t("settings.password_placeholder"))
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet(self._input_style())
        layout.addWidget(self.password_input)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        login_btn = QPushButton(self.tr.t("settings.login_button"))
        login_btn.setFixedHeight(36)
        login_btn.setStyleSheet(self._button_style())
        login_btn.clicked.connect(self._on_login_clicked)

        reset_btn = QPushButton(self.tr.t("settings.reset_button"))
        reset_btn.setFixedHeight(36)
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.c_bg_tertiary};
                color: {self.c_text_primary};
                border: 2px solid {self.c_border_light};
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                border-color: {self.c_primary};
                background-color: {self.c_bg_secondary};
            }}
        """)
        reset_btn.clicked.connect(self._on_reset_clicked)

        btn_layout.addWidget(login_btn)
        btn_layout.addWidget(reset_btn)
        layout.addLayout(btn_layout)

        return container

    def _on_login_clicked(self):
        login = self.login_input.text().strip()
        password = self.password_input.text()

        if not login or not password:
            msg_box = MessageBox(
                self.theme,
                self.tr.t("dialog.warning"),
                self.tr.t("messages.fill_all_fields"),
                MessageBox.Icon.Warning,
                self
            )
            msg_box.exec()
            return

        msg_box = MessageBox(
            self.theme,
            self.tr.t("settings.restart_required"),
            self.tr.t("settings.restart_message"),
            MessageBox.Icon.Question,
            self
        )
        yes_btn = msg_box.addButton(self.tr.t("buttons.yes"), MessageBox.ButtonRole.YesRole)
        no_btn = msg_box.addButton(self.tr.t("buttons.no"), MessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(yes_btn)

        msg_box.exec()

        if msg_box.clickedButton() == yes_btn:
            self._clear_cookies()
            restart_application(quit_app=True, login=login, password=password)

    def _on_reset_clicked(self):
        msg_box = MessageBox(
            self.theme,
            self.tr.t("settings.reset_button"),
            self.tr.t("settings.reset_success"),
            MessageBox.Icon.Information,
            self
        )
        msg_box.addButton(self.tr.t("buttons.ok"), MessageBox.ButtonRole.AcceptRole)
        msg_box.exec()

        self._clear_cookies()
        restart_application()

    def _clear_cookies(self):
        try:
            if self.main_window and hasattr(self.main_window, 'workshop_tab'):
                workshop_tab = self.main_window.workshop_tab
                if hasattr(workshop_tab, 'parser') and workshop_tab.parser:
                    workshop_tab.parser.clear_cookies()
        except Exception as e:
            print(f"Error clearing cookies: {e}")

    def _on_theme_changed(self, index):
        if 0 <= index < len(self._theme_keys):
            theme = self._theme_keys[index]
        else:
            theme = "dark"

        current_theme = self.config.get_theme()

        if theme == current_theme:
            return

        self.config.set_theme(theme)

        msg_box = MessageBox(
            self.theme,
            self.tr.t("messages.restart_title"),
            self.tr.t("messages.restart_theme_message"),
            MessageBox.Icon.Question,
            self
        )
        yes_btn = msg_box.addButton(self.tr.t("buttons.yes"), MessageBox.ButtonRole.YesRole)
        no_btn = msg_box.addButton(self.tr.t("buttons.no"), MessageBox.ButtonRole.NoRole)
        msg_box.exec()

        if msg_box.clickedButton() == yes_btn:
            restart_application()

    def _on_language_changed(self, index):
        lang_codes = list(self.tr.SUPPORTED_LANGUAGES.keys())
        lang = lang_codes[index] if index < len(lang_codes) else "en"
        self.config.set_language(lang)
        self.tr.set_language(lang)

        has_downloads = False
        has_extractions = False
        dm = None

        if self.main_window and hasattr(self.main_window, 'dm'):
            dm = self.main_window.dm
            has_downloads = len(dm.downloading) > 0
            has_extractions = len(dm.extracting) > 0

        if has_downloads or has_extractions:
            if has_downloads and has_extractions:
                msg = self.tr.t("messages.restart_with_tasks")
            elif has_downloads:
                msg = self.tr.t("messages.restart_with_downloads_only")
            else:
                msg = self.tr.t("messages.restart_with_extractions_only")
        else:
            msg = self.tr.t("messages.restart_now_question")

        msg_box = MessageBox(
            self.theme,
            self.tr.t("messages.language_changed"),
            msg,
            MessageBox.Icon.Question,
            self
        )
        yes_btn = msg_box.addButton(self.tr.t("buttons.yes"), MessageBox.ButtonRole.YesRole)
        no_btn = msg_box.addButton(self.tr.t("buttons.no"), MessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(yes_btn)

        msg_box.exec()

        if msg_box.clickedButton() == yes_btn:
            if dm:
                dm.cleanup_all()

            if self.main_window and hasattr(self.main_window, 'workshop_tab'):
                self.main_window.workshop_tab.cleanup()

            restart_application()

    def _combo_style(self):
        return f"""
            QComboBox {{
                background-color: {self.c_bg_tertiary};
                color: {self.c_text_primary};
                border: 1px solid {self.c_border};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 500;
                min-height: 18px;
            }}
            QComboBox:hover {{
                border-color: {self.c_primary};
                background-color: {self.c_bg_secondary};
            }}
            QComboBox:focus {{
                border-color: {self.c_primary};
            }}
            QComboBox::drop-down {{
                width: 0px;
                border: none;
            }}
            QComboBox::down-arrow {{
                width: 0px;
                height: 0px;
                image: none;
            }}
            QComboBox:on {{
                border-color: {self.c_primary};
                border-bottom-left-radius: 0px;
                border-bottom-right-radius: 0px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {self.c_bg_tertiary};
                color: {self.c_text_primary};
                selection-background-color: {self.c_primary};
                selection-color: {self.c_text_primary};
                border: 1px solid {self.c_primary};
                border-top: none;
                border-bottom-left-radius: 6px;
                border-bottom-right-radius: 6px;
                padding: 4px;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 10px;
                border-radius: 4px;
                margin: 2px 4px;
                min-height: 20px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background-color: {self.c_bg_secondary};
            }}
            QComboBox QAbstractItemView::item:selected {{
                background-color: {self.c_primary};
            }}
        """

    def _input_style(self):
        return f"""
            QLineEdit {{
                background-color: {self.c_bg_tertiary};
                color: {self.c_text_primary};
                border: 2px solid {self.c_border};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {self.c_primary};
            }}
        """

    def _button_style(self):
        return f"""
            QPushButton {{
                background-color: {self.c_primary};
                color: {self.c_text_primary};
                border: none;
                border-radius: 8px;
                padding: 8px;
                font-weight: 700;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {self.c_primary_hover};
            }}
        """

    def _tab_widget_style(self):
        return f"""
            QTabBar {{
                background-color: {self.c_bg_secondary};
            }}
            QTabWidget::pane {{
                background-color: transparent;
                border: 1px solid {self.c_border_light};
                border-radius: 8px;
                margin-top: 15px;
            }}
            QTabBar::tab {{
                background-color: {self.c_bg_tertiary};
                color: {self.c_text_secondary};
                border: 1px solid {self.c_border_light};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 8px 20px;
                margin-right: 2px;
                font-size: 12px;
                font-weight: 600;
            }}
            QTabBar::tab:selected {{
                background-color: {self.c_bg_secondary};
                color: {self.c_text_primary};
                border-bottom: 2px solid {self.c_primary};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {self.c_bg_secondary};
                color: {self.c_text_primary};
            }}
            QTabBar::tab:first {{
                margin-left: 0px;
            }}
        """
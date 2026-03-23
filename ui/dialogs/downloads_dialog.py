import webbrowser

from PyQt6.QtCore import QEvent, QPoint, QTimer, Qt, QSize, pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget, QPushButton

from infrastructure.resources.resource_manager import get_icon
from ui.dialogs.base_dialog import BaseDialog
from ui.widgets.preview_popup import PreviewPopup
from ui.widgets.progress import SmallCircularProgress


class DownloadsDialog(BaseDialog):
    download_cancelled = pyqtSignal(str)

    def __init__(self, translator, theme_manager, download_service, parser, parent=None):
        super().__init__(translator.t("dialog.tasks"), parent, theme_manager, icon="ICON_TASK")

        self.tr = translator
        self.dm = download_service
        self.parser = parser

        self._preview_url_cache: dict[str, str] = {}
        self._file_size_cache: dict[str, int] = {}

        self.setFixedSize(400, 400)

        self._setup_content()
        self._setup_preview_popup()
        self._setup_update_timer()

    def set_caches(self, preview_cache: dict, size_cache: dict) -> None:
        self._preview_url_cache = preview_cache
        self._file_size_cache = size_cache

    def showAt(self, global_pos: QPoint) -> None:
        self.move(global_pos)
        self.show()

    def showEvent(self, event):
        super().showEvent(event)
        self.update_timer.start()
        self._update_list()

    def hideEvent(self, event):
        self.update_timer.stop()
        self.preview_popup.hide_preview()
        self.preview_popup.force_cancel()
        super().hideEvent(event)

    def eventFilter(self, obj, event):
        if isinstance(obj, QLabel):
            pubfileid = obj.property("pubfileid")
            if pubfileid:
                if event.type() == QEvent.Type.Enter:
                    self._show_item_preview(pubfileid, obj)
                    return False
                if event.type() == QEvent.Type.Leave:
                    self.preview_popup.hide_preview()
                    return False

        return super().eventFilter(obj, event)

    def _setup_content(self) -> None:
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"""
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
            """
        )

        self.scroll_container = QWidget(scroll)
        self.scroll_container.setStyleSheet("background: transparent;")

        self.scroll_layout = QVBoxLayout(self.scroll_container)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.scroll_container)
        self.content_layout.addWidget(scroll)

    def _setup_preview_popup(self) -> None:
        self.preview_popup = PreviewPopup(self.theme, self.tr, self)

    def _setup_update_timer(self) -> None:
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_list)
        self.update_timer.setInterval(500)

    def _update_list(self) -> None:
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
            label = QLabel(self.tr.t("labels.no_tasks"), self.scroll_container)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(
                f"""
                color: {self.c_text_secondary};
                font-size: 13px;
                background-color: {self.c_bg_tertiary};
                padding: 12px 16px;
                border-radius: 8px;
                """
            )
            label.setFixedHeight(60)
            self.scroll_layout.addWidget(label)
            self.scroll_layout.addStretch()
            return

        for task_type, pubfileid, info in all_tasks:
            self._create_task_item(task_type, pubfileid, info)

        self.scroll_layout.addStretch()

    def _create_task_item(self, task_type: str, pubfileid: str, info) -> None:
        item_widget = QWidget(self.scroll_container)
        item_widget.setFixedHeight(68)
        item_widget.setStyleSheet(
            f"""
            QWidget {{
                background-color: {self.c_bg_tertiary};
                border: 2px solid {self.c_border_light};
                border-radius: 8px;
            }}
            """
        )

        item_layout = QHBoxLayout(item_widget)
        item_layout.setContentsMargins(8, 8, 10, 8)
        item_layout.setSpacing(10)

        progress = SmallCircularProgress(
            size=52,
            line_width=3,
            theme_manager=self.theme,
            parent=item_widget,
        )
        progress.setStyleSheet("border: none;")

        status_text = getattr(info, "status", "")
        file_size_bytes = self._file_size_cache.get(pubfileid, 0)
        is_extraction = task_type == "extract"

        progress.update_from_status(status_text, file_size_bytes, is_extraction)
        item_layout.addWidget(progress)

        text_container = QWidget(item_widget)
        text_container.setStyleSheet("background: transparent; border: none;")

        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(0, 0, 0, 0)
        text_layout.setSpacing(2)

        short_id = pubfileid[:12] + "..." if len(pubfileid) > 12 else pubfileid

        if task_type == "download":
            prefix = self.tr.t("labels.download_prefix", id=short_id)
        else:
            prefix = self.tr.t("labels.extract_prefix", id=short_id)

        title_label = QLabel(prefix, text_container)
        title_label.setStyleSheet(
            f"""
            color: {self.c_text_primary};
            font-size: 12px;
            font-weight: 600;
            background: transparent;
            border: none;
            """
        )
        title_label.setCursor(Qt.CursorShape.PointingHandCursor)
        title_label.setProperty("pubfileid", pubfileid)
        title_label.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        title_label.installEventFilter(self)
        title_label.mousePressEvent = lambda e, pid=pubfileid: self._on_open_browser(pid)
        text_layout.addWidget(title_label)

        display_status = status_text[:40] + "..." if len(status_text) > 40 else status_text
        if not display_status:
            display_status = self.tr.t("labels.starting")

        status_label = QLabel(display_status, text_container)
        status_label.setStyleSheet(
            f"""
            color: {self.c_text_disabled};
            font-size: 10px;
            background: transparent;
            border: none;
            """
        )
        text_layout.addWidget(status_label)

        item_layout.addWidget(text_container, 1)

        if task_type == "download":
            delete_btn = QPushButton(item_widget)
            delete_btn.setIcon(get_icon("ICON_DELETE"))
            delete_btn.setIconSize(QSize(28, 28))
            delete_btn.setFixedSize(36, 36)
            delete_btn.setStyleSheet("QPushButton { background: transparent; border: none; }")
            delete_btn.clicked.connect(lambda checked=False, pid=pubfileid: self._cancel_download(pid))
            item_layout.addWidget(delete_btn)

        self.scroll_layout.addWidget(item_widget)

    def _show_item_preview(self, pubfileid: str, widget: QWidget) -> None:
        preview_url = self._preview_url_cache.get(pubfileid)

        if not preview_url and self.parser:
            cached_item = self.parser.get_cached_item(pubfileid)
            if cached_item and cached_item.preview_url:
                preview_url = cached_item.preview_url
                self._preview_url_cache[pubfileid] = preview_url

        global_pos = widget.mapToGlobal(QPoint(-65, widget.height() // 2 + 12))
        self.preview_popup.show_preview(preview_url or "", global_pos)

    def _on_open_browser(self, pubfileid: str) -> None:
        webbrowser.open(f"https://steamcommunity.com/sharedfiles/filedetails/?id={pubfileid}")

    def _cancel_download(self, pubfileid: str) -> None:
        self.download_cancelled.emit(pubfileid)
        QTimer.singleShot(100, self._update_list)
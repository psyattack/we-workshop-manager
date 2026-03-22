from PyQt6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QRectF,
    QSize,
    Qt,
    pyqtProperty,
    pyqtSignal,
    QTimer as _QTimer,
    QPoint,
)
from PyQt6.QtGui import QColor, QBrush, QIcon, QPainter, QTransform
from PyQt6.QtWidgets import (
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QScrollBar,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from ui.widgets.background_widget import encode_image_to_base64, decode_base64_to_pixmap
from infrastructure.resources.resource_manager import get_pixmap
from shared.helpers import request_restart_or_exit
from ui.dialogs.base_dialog import BaseDialog
from ui.notifications import MessageBox
from shared.constants import APP_VERSION_DISPLAY


class SmoothScrollBar(QScrollBar):

    def __init__(self, orientation=Qt.Orientation.Vertical, parent=None):
        super().__init__(orientation, parent)
        self._target_value = self.value()

        self._anim = QPropertyAnimation(self, b"value")
        self._anim.setDuration(350)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    def scroll_to(self, target: int, duration: int = 350) -> None:
        target = max(self.minimum(), min(target, self.maximum()))
        self._target_value = target

        self._anim.stop()
        self._anim.setDuration(duration)
        self._anim.setStartValue(self.value())
        self._anim.setEndValue(target)
        self._anim.start()

    def stop_animation(self) -> None:
        self._anim.stop()

    def is_animating(self) -> bool:
        return self._anim.state() == QPropertyAnimation.State.Running


class AnimatedToggle(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, parent=None, theme_manager=None):
        super().__init__(parent)
        self.theme = theme_manager
        self._checked = False
        self._circle_position = 3.0
        self._background_color = QColor(self._c("bg_tertiary"))
        self.setFixedSize(38, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._pos_anim = QPropertyAnimation(self, b"circle_position")
        self._pos_anim.setDuration(160)
        self._pos_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self._clr_anim = QPropertyAnimation(self, b"background_color")
        self._clr_anim.setDuration(160)
        self._clr_anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

    def _c(self, name: str) -> str:
        if self.theme:
            return self.theme.get_color(name)
        return {"bg_tertiary": "#252938", "primary": "#4A7FD9", "border": "#2A2F42"}.get(name, "#FFF")

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool) -> None:
        if self._checked == checked:
            return
        self._checked = checked
        self._animate()

    def toggle(self) -> None:
        self._checked = not self._checked
        self._animate()
        self.toggled.emit(self._checked)

    def get_circle_position(self) -> float:
        return self._circle_position

    def set_circle_position(self, p: float) -> None:
        self._circle_position = p
        self.update()

    circle_position = pyqtProperty(float, get_circle_position, set_circle_position)

    def get_background_color(self) -> QColor:
        return self._background_color

    def set_background_color(self, c: QColor) -> None:
        self._background_color = c
        self.update()

    background_color = pyqtProperty(QColor, get_background_color, set_background_color)

    def _animate(self) -> None:
        self._pos_anim.stop()
        self._clr_anim.stop()
        end = self.width() - 17.0 if self._checked else 3.0
        clr = QColor(self._c("primary")) if self._checked else QColor(self._c("bg_tertiary"))
        self._pos_anim.setStartValue(self._circle_position)
        self._pos_anim.setEndValue(end)
        self._clr_anim.setStartValue(self._background_color)
        self._clr_anim.setEndValue(clr)
        self._pos_anim.start()
        self._clr_anim.start()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            self.toggle()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(self._background_color))
        p.drawRoundedRect(QRectF(0, 0, self.width(), self.height()), 10, 10)
        p.setBrush(QBrush(QColor("#FFFFFF")))
        sz = 14
        cy = (self.height() - sz) / 2
        p.drawEllipse(QRectF(self._circle_position, cy, sz, sz))


class SearchLineEdit(QFrame):
    textChanged = pyqtSignal(str)

    def __init__(self, placeholder="Search settings…", theme_manager=None, parent=None):
        super().__init__(parent)
        self.theme = theme_manager
        self.setFixedHeight(34)
        self.setObjectName("searchFrame")

        bg = self._c("bg_tertiary")
        border = self._c("border")
        primary = self._c("primary")
        txt = self._c("text_primary")
        dis = self._c("text_disabled")

        self.setStyleSheet(
            f"""
            #searchFrame {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
            }}
            #searchFrame:focus-within {{
                border-color: {primary};
            }}
            """
        )

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 0, 8, 0)
        lay.setSpacing(6)

        icon = QLabel()
        icon.setFixedSize(16, 16)
        pm = get_pixmap("ICON_SEARCH", 16)
        if not pm.isNull():
            icon.setPixmap(pm)
        else:
            icon.setText("🔍")
        icon.setStyleSheet("background:transparent;border:none;")
        lay.addWidget(icon)

        self._input = QLineEdit()
        self._input.setPlaceholderText(placeholder)
        self._input.setStyleSheet(
            f"background:transparent;border:none;color:{txt};font-size:12px;padding:0;"
        )
        self._input.textChanged.connect(self.textChanged.emit)
        lay.addWidget(self._input, 1)

        self._badge = QLabel()
        self._badge.setFixedHeight(18)
        self._badge.setStyleSheet(
            f"background:{primary};color:#fff;border-radius:9px;font-size:10px;"
            f"font-weight:700;padding:0 6px;border:none;"
        )
        self._badge.hide()
        lay.addWidget(self._badge)

        self._clear = QPushButton("✕")
        self._clear.setFixedSize(18, 18)
        self._clear.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;color:{dis};font-size:11px;border-radius:9px;}}"
            f"QPushButton:hover{{background:{bg};color:{txt};}}"
        )
        self._clear.clicked.connect(lambda: self._input.clear())
        self._clear.hide()
        lay.addWidget(self._clear)

        self._input.textChanged.connect(lambda t: self._clear.setVisible(bool(t)))

    def _c(self, n: str) -> str:
        if self.theme:
            return self.theme.get_color(n)
        return {
            "bg_tertiary": "#252938", "border": "#2A2F42",
            "primary": "#4A7FD9", "text_primary": "#FFF", "text_disabled": "#6B6E7C",
        }.get(n, "#FFF")

    def text(self) -> str:
        return self._input.text()

    def set_badge(self, count: int, active: bool) -> None:
        if active and count >= 0:
            self._badge.setText(str(count))
            self._badge.show()
        else:
            self._badge.hide()


class CategoryDivider(QWidget):
    def __init__(self, title: str, theme_manager=None, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;border:none;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(2, 6, 2, 2)
        lay.setSpacing(8)
        c = theme_manager.get_color("text_disabled") if theme_manager else "#6B6E7C"
        b = theme_manager.get_color("border") if theme_manager else "#2A2F42"
        lbl = QLabel(title.upper())
        lbl.setStyleSheet(
            f"font-size:10px;font-weight:800;color:{c};letter-spacing:1.5px;"
            f"background:transparent;border:none;"
        )
        lay.addWidget(lbl)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background:{b};border:none;max-height:1px;")
        lay.addWidget(line, 1)


class CollapsibleSection(QWidget):
    def __init__(self, title: str, parent=None, expanded: bool = True, theme_manager=None):
        super().__init__(parent)
        self.theme = theme_manager
        self._colors()
        self._expanded = expanded
        self._title = title
        self.setStyleSheet("background:transparent;border:none;")

        ml = QVBoxLayout(self)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(0)

        self._header = QPushButton()
        self._header.setCheckable(True)
        self._header.setChecked(expanded)
        self._header.clicked.connect(self._toggle)
        self._header.setFixedHeight(32)
        self._set_text()
        self._header.setStyleSheet(
            f"""
            QPushButton{{background:{self._bg2};color:{self._ts};border:1px solid {self._bd};
                border-radius:6px;padding:3px 10px;font-size:11px;font-weight:700;text-align:left;}}
            QPushButton:hover{{border-color:{self._pr};color:{self._tp};}}
            QPushButton:checked{{color:{self._tp};border-color:{self._bl};
                border-bottom-left-radius:0;border-bottom-right-radius:0;}}
            """
        )
        ml.addWidget(self._header)

        self._body = QWidget()
        self._body.setStyleSheet(
            f"QWidget{{background:{self._bg1};border:1px solid {self._bd};border-top:none;"
            f"border-bottom-left-radius:6px;border-bottom-right-radius:6px;}}"
        )
        self._body_layout = QVBoxLayout(self._body)
        self._body_layout.setContentsMargins(10, 6, 10, 8)
        self._body_layout.setSpacing(4)
        ml.addWidget(self._body)
        self._body.setVisible(expanded)

    def _colors(self):
        g = lambda n, d: self.theme.get_color(n) if self.theme else d
        self._bg1 = g("bg_secondary", "#1A1D2E")
        self._bg2 = g("bg_tertiary", "#252938")
        self._bd = g("border", "#2A2F42")
        self._bl = g("border_light", "#3A3F52")
        self._tp = g("text_primary", "#FFF")
        self._ts = g("text_secondary", "#B4B7C3")
        self._pr = g("primary", "#4A7FD9")

    def content_layout(self):
        return self._body_layout

    def add_widget(self, w):
        self._body_layout.addWidget(w)

    def add_layout(self, l):
        self._body_layout.addLayout(l)

    def set_expanded(self, e: bool):
        self._expanded = e
        self._header.setChecked(e)
        self._set_text()
        self._body.setVisible(e)

    def _set_text(self):
        a = "▾" if self._expanded else "▸"
        self._header.setText(f" {a}  {self._title}")

    def _toggle(self, c):
        self._expanded = c
        self._set_text()
        self._body.setVisible(c)


class SettingsField(QWidget):
    def __init__(
        self, label_text: str, control_widget, description: str = None,
        stacked: bool = False, parent=None, theme_manager=None,
    ):
        super().__init__(parent)
        self.theme = theme_manager
        self._lbl = label_text or ""
        self._desc = description or ""
        ts = (theme_manager.get_color("text_secondary") if theme_manager else "#B4B7C3")
        td = (theme_manager.get_color("text_disabled") if theme_manager else "#6B6E7C")
        self.setStyleSheet("background:transparent;border:none;")

        if stacked:
            lay = QVBoxLayout(self)
            lay.setContentsMargins(0, 0, 0, 0)
            lay.setSpacing(2)
            if label_text:
                l = QLabel(label_text)
                l.setStyleSheet(f"font-size:11px;font-weight:600;color:{ts};background:transparent;border:none;")
                lay.addWidget(l)
            if description:
                d = QLabel(description)
                d.setWordWrap(True)
                d.setStyleSheet(f"font-size:10px;color:{td};background:transparent;border:none;")
                lay.addWidget(d)
            lay.addWidget(control_widget)
            return

        lay = QHBoxLayout(self)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(8)

        left = QVBoxLayout()
        left.setSpacing(0)
        if label_text:
            l = QLabel(label_text)
            l.setStyleSheet(f"font-size:11px;font-weight:600;color:{ts};background:transparent;border:none;")
            left.addWidget(l)
        if description:
            d = QLabel(description)
            d.setWordWrap(True)
            d.setStyleSheet(f"font-size:10px;color:{td};background:transparent;border:none;")
            left.addWidget(d)
        lay.addLayout(left, 1)

        if isinstance(control_widget, AnimatedToggle):
            lay.addWidget(control_widget, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        elif isinstance(control_widget, QComboBox):
            control_widget.setFixedWidth(130)
            control_widget.setFixedHeight(26)
            lay.addWidget(control_widget, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        else:
            control_widget.setFixedWidth(140)
            lay.addWidget(control_widget, 0, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

    def searchable_text(self) -> str:
        return f"{self._lbl} {self._desc}".lower()


class SpinningIconLabel(QLabel):
    def __init__(self, icon_name: str, size: int = 14, parent=None):
        super().__init__(parent)
        self._base = get_pixmap(icon_name, size)
        self._angle = 0
        self._sz = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background:transparent;border:none;")
        self._t = _QTimer(self)
        self._t.timeout.connect(self._rot)
        self._t.setInterval(30)

    def start(self):
        self._t.start()

    def stop(self):
        self._t.stop()
        self._angle = 0
        if not self._base.isNull():
            self.setPixmap(self._base)

    def _rot(self):
        self._angle = (self._angle + 5) % 360
        tf = QTransform()
        tf.rotate(self._angle)
        r = self._base.transformed(tf, Qt.TransformationMode.SmoothTransformation)
        x = max(0, (r.width() - self._sz) // 2)
        y = max(0, (r.height() - self._sz) // 2)
        self.setPixmap(r.copy(x, y, self._sz, self._sz))


class SettingsDialog(BaseDialog):
    def __init__(self, config, accounts, translator, theme_manager, main_window, parent=None):
        super().__init__(
            translator.t("settings.title"), parent, theme_manager, icon="ICON_SETTINGS"
        )
        self.config = config
        self.accounts = accounts
        self.tr = translator
        self.main_window = main_window
        self.setFixedSize(900, 640)
        self._apply_container_style()
        self._section_fields: dict[CollapsibleSection, list] = {}
        self._category_groups: dict[CategoryDivider, list] = {}
        self._nav_buttons: list[QPushButton] = []
        self._manual_nav = False
        self._smooth_sb: SmoothScrollBar | None = None
        self._setup_ui()

    def _t(self, key: str, fallback: str = "") -> str:
        v = self.tr.t(key)
        return v if v != key else (fallback or key.split(".")[-1].replace("_", " ").title())

    def _reg(self, section, field):
        self._section_fields.setdefault(section, []).append(field)

    def _mk_searchable(self, widget, keywords: str):
        widget.searchable_text = lambda: keywords.lower()

    def _make_nav_icon(self, icon_name: str, size: int = 14) -> QIcon:
        pm = get_pixmap(icon_name, size)
        if not pm.isNull():
            return QIcon(pm)
        return QIcon()

    def _setup_ui(self) -> None:
        self.content_layout.setSpacing(6)

        self._search = SearchLineEdit(
            placeholder=self._t("settings.search_placeholder", "Search settings…"),
            theme_manager=self.theme,
        )
        self._search.textChanged.connect(self._on_search)
        self.content_layout.addWidget(self._search)

        body = QWidget()
        body.setStyleSheet("background:transparent;border:none;")
        h = QHBoxLayout(body)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        h.addWidget(self._build_sidebar())

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background:{self.c_border};border:none;")
        h.addWidget(sep)

        self._scroll = self._build_scroll()
        h.addWidget(self._scroll, 1)

        self.content_layout.addWidget(body, 1)
        self._nav_buttons[0].setChecked(True)

    def _build_sidebar(self) -> QWidget:
        sb = QWidget()
        sb.setFixedWidth(140)
        sb.setStyleSheet(f"background:{self.c_bg_secondary};border:none;")
        vl = QVBoxLayout(sb)
        vl.setContentsMargins(6, 8, 6, 8)
        vl.setSpacing(2)

        grp = QButtonGroup(self)
        grp.setExclusive(True)

        entries = [
            (self._t("settings.tab_general", "General"), "ICON_HOME"),
            (self._t("settings.tab_account", "Account"), "ICON_USER"),
            (self._t("settings.tab_advanced", "Advanced"), "ICON_STAR"),
        ]
        for i, (label, icon_name) in enumerate(entries):
            btn = QPushButton(f"  {label}")
            btn.setCheckable(True)
            btn.setFixedHeight(34)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setIcon(self._make_nav_icon(icon_name, 14))
            btn.setIconSize(QSize(14, 14))
            btn.setStyleSheet(self._nav_btn_style())
            btn.clicked.connect(lambda _, idx=i: self._scroll_to_cat(idx))
            grp.addButton(btn, i)
            vl.addWidget(btn)
            self._nav_buttons.append(btn)

        vl.addStretch()

        ver = QLabel(APP_VERSION_DISPLAY)
        ver.setStyleSheet(
            f"font-size:10px;color:{self.c_text_disabled};background:transparent;border:none;"
        )
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(ver)

        return sb

    def _nav_btn_style(self) -> str:
        return f"""
        QPushButton{{
            background:transparent;color:{self.c_text_secondary};border:none;
            border-left:3px solid transparent;text-align:left;padding:6px 10px;
            font-size:12px;font-weight:600;border-radius:0;
        }}
        QPushButton:hover{{background:{self.c_bg_tertiary};color:{self.c_text_primary};}}
        QPushButton:checked{{
            background:rgba(74,127,217,0.08);color:{self.c_primary};
            border-left:3px solid {self.c_primary};font-weight:700;
        }}
        """

    def _build_scroll(self) -> QScrollArea:
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        sa.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._smooth_sb = SmoothScrollBar(Qt.Orientation.Vertical, sa)
        sa.setVerticalScrollBar(self._smooth_sb)

        self._smooth_sb.valueChanged.connect(self._on_scroll_moved)

        sa.setStyleSheet(
            f"""
            QScrollArea{{background:transparent;border:none;}}
            QScrollArea>QWidget>QWidget{{background:transparent;}}
            QScrollBar:vertical{{
                width:0px;
                background:transparent;
            }}
            QScrollBar::handle:vertical{{
                background:transparent;
            }}
            QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{{
                height:0px;
            }}
            QScrollBar::add-page:vertical,QScrollBar::sub-page:vertical{{
                background:transparent;
            }}
            """
        )
        inner = QWidget()
        inner.setStyleSheet("background:transparent;")
        self._inner = QVBoxLayout(inner)
        self._inner.setContentsMargins(12, 6, 8, 8)
        self._inner.setSpacing(8)

        self._dividers: list[CategoryDivider] = []
        self._build_general()
        self._build_account()
        self._build_advanced()
        self._build_no_results()
        self._inner.addStretch()

        sa.setWidget(inner)
        return sa

    def _build_general(self):
        div = CategoryDivider(self._t("settings.tab_general", "General"), self.theme)
        self._inner.addWidget(div)
        self._dividers.append(div)

        sec = CollapsibleSection(
            self._t("settings.appearance", "Appearance"), expanded=True, theme_manager=self.theme
        )

        f1 = SettingsField(
            self._t("settings.theme_dev", "Theme"), self._create_theme_combo(),
            description=self._t("settings.theme_description", "Visual theme for the application"),
            theme_manager=self.theme,
        )
        sec.add_widget(f1)
        self._reg(sec, f1)

        f2 = SettingsField(
            self._t("settings.language", "Language"), self._create_language_combo(),
            description=self._t("settings.language_description", "Interface language (requires restart)"),
            theme_manager=self.theme,
        )
        sec.add_widget(f2)
        self._reg(sec, f2)

        f3 = SettingsField(
            self._t("settings.show_id_section", "Show ID Section"), self._create_show_id_toggle(),
            description=self._t("settings.show_id_description", "Show or hide the ID section"),
            theme_manager=self.theme,
        )
        sec.add_widget(f3)
        self._reg(sec, f3)

        self._inner.addWidget(sec)
        self._category_groups.setdefault(div, []).append(sec)

        sec2 = CollapsibleSection(
            self._t("settings.behavior", "Behavior"), expanded=True, theme_manager=self.theme
        )
        for label_key, desc_key, factory in [
            ("labels.minimize_on_apply", "settings.minimize_description", self._create_minimize_toggle),
            ("settings.preload_next_page", "settings.preload_description", self._create_preload_toggle),
            ("settings.auto_check_updates", "settings.auto_check_updates_description", self._create_auto_updates_toggle),
            ("settings.save_window_state", "settings.save_window_state_description", self._create_save_window_state_toggle),
        ]:
            f = SettingsField(
                self._t(label_key), factory(),
                description=self._t(desc_key),
                theme_manager=self.theme,
            )
            sec2.add_widget(f)
            self._reg(sec2, f)

        self._inner.addWidget(sec2)
        self._category_groups[div].append(sec2)

    def _build_account(self):
        div = CategoryDivider(self._t("settings.tab_account", "Account"), self.theme)
        self._inner.addWidget(div)
        self._dividers.append(div)

        sec = CollapsibleSection(
            self._t("settings.account_selection", "Account Selection"),
            expanded=True, theme_manager=self.theme,
        )
        f1 = SettingsField(
            self._t("settings.account", "Account"), self._create_account_combo(),
            description=self._t("settings.account_description", "Select the active Steam account"),
            theme_manager=self.theme,
        )
        sec.add_widget(f1)
        self._reg(sec, f1)
        self._inner.addWidget(sec)
        self._category_groups.setdefault(div, []).append(sec)

        sec2 = CollapsibleSection(
            self._t("settings.steam_login", "Steam Login"),
            expanded=False, theme_manager=self.theme,
        )
        login_w = self._create_steam_login_section()
        self._mk_searchable(login_w, "steam login password credentials account authentication")
        sec2.add_widget(login_w)
        self._reg(sec2, login_w)
        self._inner.addWidget(sec2)
        self._category_groups[div].append(sec2)

    def _build_advanced(self):
        div = CategoryDivider(self._t("settings.tab_advanced", "Advanced"), self.theme)
        self._inner.addWidget(div)
        self._dividers.append(div)

        meta_sec = self._create_metadata_init_section()
        self._inner.addWidget(meta_sec)
        self._category_groups.setdefault(div, []).append(meta_sec)

        bg_sec = self._create_background_section()
        self._inner.addWidget(bg_sec)
        self._category_groups[div].append(bg_sec)

        sec = CollapsibleSection(
            self._t("settings.debug", "Debug"), expanded=False, theme_manager=self.theme
        )
        f = SettingsField(
            self._t("settings.debug_mode", "Debug Mode"), self._create_debug_toggle(),
            description=self._t("settings.debug_description", "Enable debug mode for webview testing"),
            theme_manager=self.theme,
        )
        sec.add_widget(f)
        self._reg(sec, f)
        self._inner.addWidget(sec)
        self._category_groups[div].append(sec)

    def _build_no_results(self):
        self._no_results = QWidget()
        self._no_results.setStyleSheet("background:transparent;border:none;")
        vl = QVBoxLayout(self._no_results)
        vl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.setSpacing(6)
        vl.setContentsMargins(0, 50, 0, 50)

        ic = QLabel()
        pm = get_pixmap("ICON_SEARCH", 28)
        if not pm.isNull():
            ic.setPixmap(pm)
        ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ic.setStyleSheet("background:transparent;border:none;")
        vl.addWidget(ic)

        t1 = QLabel(self._t("settings.no_results", "No settings found"))
        t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t1.setStyleSheet(
            f"font-size:13px;font-weight:600;color:{self.c_text_secondary};background:transparent;border:none;"
        )
        vl.addWidget(t1)

        t2 = QLabel(self._t("settings.no_results_hint", "Try a different search term"))
        t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t2.setStyleSheet(
            f"font-size:11px;color:{self.c_text_disabled};background:transparent;border:none;"
        )
        vl.addWidget(t2)

        self._no_results.hide()
        self._inner.addWidget(self._no_results)

    def _on_search(self, text: str) -> None:
        q = text.lower().strip()
        total = 0

        for section, fields in self._section_fields.items():
            vis = False
            for f in fields:
                match = not q or q in f.searchable_text()
                f.setVisible(match)
                if match:
                    vis = True
                    total += 1
            if q:
                section.setVisible(vis)
                if vis:
                    section.set_expanded(True)
            else:
                section.setVisible(True)

        for div, secs in self._category_groups.items():
            if q:
                div.setVisible(any(s.isVisible() for s in secs))
            else:
                div.setVisible(True)

        self._no_results.setVisible(total == 0 and bool(q))
        self._search.set_badge(total, bool(q))

    def _scroll_to_cat(self, idx: int) -> None:
        self._manual_nav = True

        if idx < len(self._nav_buttons):
            self._nav_buttons[idx].setChecked(True)

        if not self._smooth_sb:
            self._manual_nav = False
            return

        if idx == len(self._dividers) - 1:
            target = self._smooth_sb.maximum()
        elif idx < len(self._dividers):
            w = self._dividers[idx]
            y = w.mapTo(self._scroll.widget(), QPoint(0, 0)).y()
            target = max(0, y - 4)
        else:
            self._manual_nav = False
            return

        distance = abs(self._smooth_sb.value() - target)
        duration = min(500, max(200, int(distance * 0.8)))

        self._smooth_sb.scroll_to(target, duration)

        unlock_delay = duration + 50
        _QTimer.singleShot(unlock_delay, self._reset_manual_nav)

    def _reset_manual_nav(self) -> None:
        self._manual_nav = False

    def _on_scroll_moved(self, value: int) -> None:
        if self._manual_nav:
            return
        if not self._dividers:
            return

        sb = self._smooth_sb or self._scroll.verticalScrollBar()

        if sb.maximum() > 0 and value >= sb.maximum() - 5:
            active = len(self._dividers) - 1
        else:
            active = 0
            for i, d in enumerate(self._dividers):
                y = d.mapTo(self._scroll.widget(), QPoint(0, 0)).y()
                if value >= y - 30:
                    active = i

        if active < len(self._nav_buttons):
            self._nav_buttons[active].setChecked(True)

    def _create_account_combo(self) -> QComboBox:
        c = QComboBox()
        last = 1
        for i in range(len(self.accounts.get_accounts()) - last):
            c.addItem(f"{self.tr.t('labels.account')} {i + 1}")
        c.setCurrentIndex(self.config.get_account_number())
        c.currentIndexChanged.connect(lambda idx: self.config.set_account_number(idx))
        c.setStyleSheet(self._combo_style())
        return c

    def _create_theme_combo(self) -> QComboBox:
        c = QComboBox()
        self._theme_keys = list(self.theme.get_available_themes())
        for k in self._theme_keys:
            tk = f"labels.theme_{k}"
            c.addItem(self.tr.t(tk) if self.tr.t(tk) != tk else k.capitalize())
        cur = self.config.get_theme()
        if cur in self._theme_keys:
            c.setCurrentIndex(self._theme_keys.index(cur))
        c.currentIndexChanged.connect(self._on_theme_changed)
        c.setStyleSheet(self._combo_style())
        return c

    def _create_language_combo(self) -> QComboBox:
        c = QComboBox()
        langs = list(self.tr.get_available_languages().values())
        c.addItems(langs)
        codes = list(self.tr.get_available_languages().keys())
        cur = self.config.get_language()
        c.setCurrentIndex(codes.index(cur) if cur in codes else 0)
        c.currentIndexChanged.connect(self._on_language_changed)
        c.setStyleSheet(self._combo_style())
        return c

    def _create_show_id_toggle(self):
        t = AnimatedToggle(theme_manager=self.theme)
        t.setChecked(self.config.get_show_id_section())
        t.toggled.connect(self._on_show_id_changed)
        return t

    def _create_preload_toggle(self):
        t = AnimatedToggle(theme_manager=self.theme)
        t.setChecked(self.config.get_preload_next_page())
        t.toggled.connect(self._on_preload_changed)
        return t

    def _create_auto_updates_toggle(self):
        t = AnimatedToggle(theme_manager=self.theme)
        t.setChecked(self.config.get_auto_check_updates())
        t.toggled.connect(self._on_auto_updates_changed)
        return t

    def _create_save_window_state_toggle(self):
        t = AnimatedToggle(theme_manager=self.theme)
        t.setChecked(self.config.get_save_window_state())
        t.toggled.connect(self._on_save_window_state_changed)
        return t

    def _create_minimize_toggle(self):
        t = AnimatedToggle(theme_manager=self.theme)
        t.setChecked(self.config.get_minimize_on_apply())
        t.toggled.connect(self._on_minimize_changed)
        return t

    def _create_debug_toggle(self):
        t = AnimatedToggle(theme_manager=self.theme)
        t.setChecked(self.config.get_debug_mode())
        t.toggled.connect(self._on_debug_mode_changed)
        return t

    def _create_steam_login_section(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background:transparent;border:none;")
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(6)

        desc = QLabel(self._t("settings.login_description", "Enter your Steam credentials"))
        desc.setWordWrap(True)
        desc.setStyleSheet(
            f"font-size:10px;color:{self.c_text_disabled};background:transparent;border:none;"
        )
        vl.addWidget(desc)

        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText(self.tr.t("settings.login_placeholder"))
        self.login_input.setFixedHeight(30)
        self.login_input.setStyleSheet(self._input_style())
        vl.addWidget(self.login_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(self.tr.t("settings.password_placeholder"))
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(30)
        self.password_input.setStyleSheet(self._input_style())
        vl.addWidget(self.password_input)

        bl = QHBoxLayout()
        bl.setSpacing(6)
        lb = QPushButton(self.tr.t("settings.login_button"))
        lb.setFixedHeight(28)
        lb.setStyleSheet(self._compact_btn(True))
        lb.clicked.connect(self._on_login_clicked)
        rb = QPushButton(self.tr.t("settings.reset_button"))
        rb.setFixedHeight(28)
        rb.setStyleSheet(self._compact_btn(False))
        rb.clicked.connect(self._on_reset_clicked)
        bl.addWidget(lb)
        bl.addWidget(rb)
        vl.addLayout(bl)
        return w

    def _create_metadata_init_section(self) -> CollapsibleSection:
        sec = CollapsibleSection(
            self._t("settings.metadata_init", "Metadata Initialization"),
            expanded=True, theme_manager=self.theme,
        )

        toggle = AnimatedToggle(theme_manager=self.theme)
        toggle.setChecked(self.config.get_auto_init_metadata())
        toggle.toggled.connect(lambda c: self.config.set_auto_init_metadata(c))
        f = SettingsField(
            self._t("settings.auto_init_metadata", "Auto-initialize on startup"), toggle,
            description=self._t("settings.auto_init_metadata_description",
                                "Fetch metadata for all wallpapers on start"),
            theme_manager=self.theme,
        )
        sec.add_widget(f)
        self._reg(sec, f)

        sc = QWidget()
        sc.setStyleSheet("background:transparent;border:none;")
        sl = QHBoxLayout(sc)
        sl.setContentsMargins(2, 0, 2, 0)
        sl.setSpacing(6)
        self._init_status_label = QLabel()
        self._init_status_label.setStyleSheet(
            f"font-size:10px;color:{self.c_text_secondary};background:transparent;border:none;"
        )
        self._init_spinner = SpinningIconLabel("ICON_REFRESH", 14)
        self._init_spinner.hide()

        init_btn = QPushButton(self._t("settings.initialize_now", "Initialize Now"))
        init_btn.setFixedHeight(24)
        init_btn.setStyleSheet(self._compact_btn(True))
        init_btn.clicked.connect(self._on_manual_init_clicked)
        self._init_btn = init_btn

        sl.addWidget(self._init_status_label, 1)
        sl.addWidget(self._init_spinner)
        sl.addWidget(init_btn)

        self._mk_searchable(sc, "metadata initialize wallpaper init startup")
        sec.add_widget(sc)
        self._reg(sec, sc)

        self._update_init_status()
        self._init_status_timer = _QTimer(self)
        self._init_status_timer.timeout.connect(self._update_init_status)
        self._init_status_timer.start(1000)

        return sec

    def _create_background_section(self) -> CollapsibleSection:
        sec = CollapsibleSection(
            self._t("settings.backgrounds", "Backgrounds"),
            expanded=False, theme_manager=self.theme,
        )
        areas = [
            ("main", self._t("settings.bg_main", "Main")),
            ("tabs", self._t("settings.bg_tabs", "Tabs")),
            ("details", self._t("settings.bg_details", "Details")),
        ]
        for key, label in areas:
            row = self._build_bg_area_row(key, label)
            self._mk_searchable(row, f"background {label} blur opacity image wallpaper")
            sec.add_widget(row)
            self._reg(sec, row)

        ext = AnimatedToggle(theme_manager=self.theme)
        ext.setChecked(self.config.get_background_extend_titlebar())
        ext.toggled.connect(self._on_extend_titlebar_changed)
        f = SettingsField(
            self._t("settings.bg_extend_titlebar", "Extend to Title Bar"), ext,
            description=self._t("settings.bg_extend_titlebar_desc",
                                "Main background covers the title bar area"),
            theme_manager=self.theme,
        )
        sec.add_widget(f)
        self._reg(sec, f)
        return sec

    def _build_bg_area_row(self, area: str, label: str) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background:transparent;border:none;")
        hl = QHBoxLayout(w)
        hl.setContentsMargins(0, 1, 0, 1)
        hl.setSpacing(6)

        preview = QLabel()
        preview.setFixedSize(32, 32)
        preview.setStyleSheet(
            f"background:{self.c_bg_tertiary};border-radius:4px;border:1px solid {self.c_border};"
        )
        preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_bg_preview(preview, area)
        hl.addWidget(preview)

        mid = QVBoxLayout()
        mid.setContentsMargins(0, 0, 0, 0)
        mid.setSpacing(1)
        hdr = QLabel(label)
        hdr.setStyleSheet(
            f"font-size:10px;font-weight:700;color:{self.c_text_primary};background:transparent;border:none;"
        )
        mid.addWidget(hdr)
        mid.addLayout(self._make_slider_row(
            self._t("settings.bg_blur", "Blur"),
            self.config.get_background_blur(area),
            lambda v, a=area: self._on_bg_blur(a, v),
        ))
        mid.addLayout(self._make_slider_row(
            self._t("settings.bg_opacity", "Opacity"),
            self.config.get_background_opacity(area),
            lambda v, a=area: self._on_bg_opacity(a, v),
        ))
        hl.addLayout(mid, 1)

        bc = QVBoxLayout()
        bc.setContentsMargins(0, 0, 0, 0)
        bc.setSpacing(2)
        sb = QPushButton(self._t("settings.bg_select", "Select"))
        sb.setFixedSize(48, 18)
        sb.setStyleSheet(self._tiny_btn())
        sb.clicked.connect(lambda _, a=area, p=preview: self._on_bg_select(a, p))
        bc.addWidget(sb)
        cb = QPushButton(self._t("settings.bg_clear", "Clear"))
        cb.setFixedSize(48, 18)
        cb.setStyleSheet(self._tiny_btn())
        cb.clicked.connect(lambda _, a=area, p=preview: self._on_bg_clear(a, p))
        bc.addWidget(cb)
        hl.addLayout(bc)
        return w

    def _make_slider_row(self, label: str, val: int, cb) -> QHBoxLayout:
        r = QHBoxLayout()
        r.setContentsMargins(0, 0, 0, 0)
        r.setSpacing(4)
        l = QLabel(label)
        l.setFixedWidth(40)
        l.setStyleSheet(
            f"font-size:10px;color:{self.c_text_secondary};background:transparent;border:none;"
        )
        s = QSlider(Qt.Orientation.Horizontal)
        s.setRange(0, 100)
        s.setValue(val)
        s.setFixedHeight(16)
        s.setStyleSheet(self._slider_style())
        vl = QLabel(f"{val}%")
        vl.setFixedWidth(28)
        vl.setStyleSheet(
            f"font-size:10px;color:{self.c_text_primary};background:transparent;border:none;"
        )
        s.valueChanged.connect(lambda v: vl.setText(f"{v}%"))
        s.valueChanged.connect(cb)
        r.addWidget(l)
        r.addWidget(s, 1)
        r.addWidget(vl)
        return r

    def _on_show_id_changed(self, checked: bool) -> None:
        self.config.set_show_id_section(checked)
        if self.main_window:
            for tab in ("wallpapers_tab", "workshop_tab"):
                t = getattr(self.main_window, tab, None)
                if t and hasattr(t, "details_panel"):
                    t.details_panel._update_id_section_visibility()

    def _on_preload_changed(self, c):
        self.config.set_preload_next_page(c)

    def _on_auto_updates_changed(self, c):
        self.config.set_auto_check_updates(c)

    def _on_save_window_state_changed(self, c):
        self.config.set_save_window_state(c)

    def _on_minimize_changed(self, c):
        self.config.set_minimize_on_apply(c)

    def _on_debug_mode_changed(self, checked: bool) -> None:
        cur = self.config.get_debug_mode()
        if checked == cur:
            return
        self.config.set_debug_mode(checked)
        mb = MessageBox(
            self.theme, self.tr.t("messages.restart_title"),
            self.tr.t("messages.restart_debug_message"),
            MessageBox.Icon.Question, self,
        )
        y = mb.addButton(self.tr.t("buttons.yes"), MessageBox.ButtonRole.YesRole)
        mb.addButton(self.tr.t("buttons.no"), MessageBox.ButtonRole.NoRole)
        mb.exec()
        if mb.clickedButton() == y:
            self._cleanup_before_restart_or_exit()
            request_restart_or_exit()

    def _on_theme_changed(self, idx: int) -> None:
        theme = self._theme_keys[idx] if 0 <= idx < len(self._theme_keys) else "dark"
        if theme == self.config.get_theme():
            return
        self.config.set_theme(theme)
        mb = MessageBox(
            self.theme, self.tr.t("messages.restart_title"),
            self.tr.t("messages.restart_theme_message"),
            MessageBox.Icon.Question, self,
        )
        y = mb.addButton(self.tr.t("buttons.yes"), MessageBox.ButtonRole.YesRole)
        mb.addButton(self.tr.t("buttons.no"), MessageBox.ButtonRole.NoRole)
        mb.exec()
        if mb.clickedButton() == y:
            self._cleanup_before_restart_or_exit()
            request_restart_or_exit()

    def _on_language_changed(self, idx: int) -> None:
        codes = list(self.tr.get_available_languages().keys())
        lang = codes[idx] if idx < len(codes) else "en"
        self.config.set_language(lang)
        self.tr.set_language(lang)

        ds = getattr(self.main_window, "dm", None) if self.main_window else None
        hd = ds and len(ds.downloading) > 0 if ds else False
        he = ds and len(ds.extracting) > 0 if ds else False

        if hd and he:
            msg = self.tr.t("messages.restart_with_tasks")
        elif hd:
            msg = self.tr.t("messages.restart_with_downloads_only")
        elif he:
            msg = self.tr.t("messages.restart_with_extractions_only")
        else:
            msg = self.tr.t("messages.restart_now_question")

        mb = MessageBox(
            self.theme, self.tr.t("messages.language_changed"), msg,
            MessageBox.Icon.Question, self,
        )
        y = mb.addButton(self.tr.t("buttons.yes"), MessageBox.ButtonRole.YesRole)
        mb.addButton(self.tr.t("buttons.no"), MessageBox.ButtonRole.NoRole)
        mb.setDefaultButton(y)
        mb.exec()
        if mb.clickedButton() == y:
            self._cleanup_before_restart_or_exit(ds)
            request_restart_or_exit()

    def _on_login_clicked(self) -> None:
        login = self.login_input.text().strip()
        pw = self.password_input.text()
        if not login or not pw:
            MessageBox(
                self.theme, self.tr.t("dialog.warning"),
                self.tr.t("settings.fill_all_fields"),
                MessageBox.Icon.Warning, self,
            ).exec()
            return
        mb = MessageBox(
            self.theme, self.tr.t("messages.restart_title"),
            self.tr.t("settings.restart_message"),
            MessageBox.Icon.Question, self,
        )
        y = mb.addButton(self.tr.t("buttons.yes"), MessageBox.ButtonRole.YesRole)
        mb.addButton(self.tr.t("buttons.no"), MessageBox.ButtonRole.NoRole)
        mb.setDefaultButton(y)
        mb.exec()
        if mb.clickedButton() == y:
            self._clear_cookies()
            self._cleanup_before_restart_or_exit()
            request_restart_or_exit(quit_app=True, login=login, password=pw)

    def _on_reset_clicked(self) -> None:
        mb = MessageBox(
            self.theme, self.tr.t("settings.reset_button"),
            self.tr.t("settings.reset_success"),
            MessageBox.Icon.Information, self,
        )
        mb.addButton(self.tr.t("buttons.ok"), MessageBox.ButtonRole.AcceptRole)
        mb.exec()
        self._clear_cookies()
        self._cleanup_before_restart_or_exit()
        request_restart_or_exit()

    def _clear_cookies(self) -> None:
        try:
            wt = getattr(self.main_window, "workshop_tab", None)
            if wt and hasattr(wt, "parser") and wt.parser:
                wt.parser.clear_cookies()
        except Exception:
            pass

    def _cleanup_before_restart_or_exit(self, download_service=None) -> None:
        if download_service is None and self.main_window and hasattr(self.main_window, "dm"):
            download_service = self.main_window.dm
        if download_service:
            try:
                download_service.cleanup_all()
            except Exception:
                pass
        if self.main_window and hasattr(self.main_window, "workshop_tab"):
            try:
                self.main_window.workshop_tab.cleanup()
            except Exception:
                pass

    def _update_init_status(self) -> None:
        if not hasattr(self, "_init_status_label"):
            return
        ini = None
        if self.main_window and hasattr(self.main_window, "get_metadata_initializer"):
            ini = self.main_window.get_metadata_initializer()
        running = ini is not None and ini.is_running
        if running:
            self._init_spinner.show()
            self._init_spinner.start()
            self._init_btn.setEnabled(False)
            if not getattr(self, "_init_progress_connected", False):
                try:
                    ini.progress_updated.connect(self._on_init_progress)
                    self._init_progress_connected = True
                except Exception:
                    pass
        else:
            self._init_spinner.stop()
            self._init_spinner.hide()
            self._init_btn.setEnabled(True)
            self._worker_connected = False
            mw = self.main_window
            if mw and hasattr(mw, "we") and hasattr(mw, "metadata_service"):
                installed = mw.we.get_installed_wallpapers()
                total = len(installed)
                uninit = mw.metadata_service.get_uninitialized_pubfileids(installed)
                done = total - len(uninit)
                if not uninit:
                    self._init_status_label.setText(
                        self._t("settings.all_initialized", f"✓ All {total} initialized").format(total=total)
                    )
                    self._init_status_label.setStyleSheet(
                        "font-size:10px;color:#5BEF9D;background:transparent;border:none;"
                    )
                else:
                    self._init_status_label.setText(f"{done} / {total}")
                    self._init_status_label.setStyleSheet(
                        f"font-size:10px;color:{self.c_text_secondary};background:transparent;border:none;"
                    )
            else:
                self._init_status_label.setText("—")

    def _on_init_progress(self, cur: int, total: int) -> None:
        if hasattr(self, "_init_status_label"):
            self._init_status_label.setText(f"{cur} / {total}")
            self._init_status_label.setStyleSheet(
                f"font-size:10px;color:{self.c_text_primary};background:transparent;border:none;"
            )

    def _on_manual_init_clicked(self) -> None:
        if not self.main_window:
            return
        if hasattr(self.main_window, "is_metadata_init_running") and self.main_window.is_metadata_init_running():
            return
        if hasattr(self.main_window, "_start_metadata_init"):
            self.main_window._start_metadata_init()
            ini = self.main_window.get_metadata_initializer()
            if ini:
                try:
                    ini.progress_updated.connect(self._on_init_progress)
                    self._init_progress_connected = True
                except Exception:
                    pass
            self._update_init_status()

    def _update_bg_preview(self, preview: QLabel, area: str) -> None:
        b64 = self.config.get_background_image(area)
        if b64:
            pm = decode_base64_to_pixmap(b64)
            if not pm.isNull():
                preview.setPixmap(pm.scaled(
                    30, 30, Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                ))
                return
        preview.setText("—")

    def _on_bg_select(self, area: str, preview: QLabel) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Background", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*)",
        )
        if not path:
            return
        b64 = encode_image_to_base64(path)
        if b64:
            self.config.set_background_image(area, b64)
            self._update_bg_preview(preview, area)
            self._apply_bg_to_window()

    def _on_bg_clear(self, area, preview):
        self.config.set_background_image(area, "")
        self._update_bg_preview(preview, area)
        self._apply_bg_to_window()

    def _on_bg_blur(self, area, v):
        self.config.set_background_blur(area, v)
        self._apply_bg_to_window()

    def _on_bg_opacity(self, area, v):
        self.config.set_background_opacity(area, v)
        self._apply_bg_to_window()

    def _on_extend_titlebar_changed(self, c):
        self.config.set_background_extend_titlebar(c)
        self._apply_bg_to_window()

    def _apply_bg_to_window(self):
        if self.main_window and hasattr(self.main_window, "apply_backgrounds"):
            self.main_window.apply_backgrounds()

    def _combo_style(self) -> str:
        return f"""
        QComboBox{{
            background-color:{self.c_bg_tertiary};color:{self.c_text_primary};
            border:1px solid {self.c_border};border-radius:5px;
            padding:4px 8px;font-size:11px;font-weight:500;min-height:16px;
        }}
        QComboBox:hover{{border-color:{self.c_primary};}}
        QComboBox::drop-down{{width:0;border:none;}}
        QComboBox::down-arrow{{width:0;height:0;image:none;}}
        QComboBox:on{{border-color:{self.c_primary};border-bottom-left-radius:0;border-bottom-right-radius:0;}}
        QComboBox QAbstractItemView{{
            background-color:{self.c_bg_tertiary};color:{self.c_text_primary};
            selection-background-color:{self.c_primary};selection-color:{self.c_text_primary};
            border:1px solid {self.c_primary};border-top:none;
            border-bottom-left-radius:5px;border-bottom-right-radius:5px;
            padding:3px;outline:none;
        }}
        QComboBox QAbstractItemView::item{{
            padding:4px 8px;border-radius:3px;margin:1px 3px;min-height:18px;
        }}
        QComboBox QAbstractItemView::item:hover{{background-color:{self.c_bg_secondary};}}
        QComboBox QAbstractItemView::item:selected{{background-color:{self.c_primary};}}
        """

    def _input_style(self) -> str:
        return f"""
        QLineEdit{{
            background-color:{self.c_bg_tertiary};color:{self.c_text_primary};
            border:1px solid {self.c_border};border-radius:6px;
            padding:5px 10px;font-size:12px;
        }}
        QLineEdit:focus{{border-color:{self.c_primary};}}
        """

    def _compact_btn(self, primary: bool = False) -> str:
        if primary:
            return f"""
            QPushButton{{
                background-color:{self.c_primary};color:{self.c_text_primary};border:none;
                border-radius:5px;padding:4px 14px;font-weight:600;font-size:11px;
            }}
            QPushButton:hover{{background-color:{self.c_primary_hover};}}
            QPushButton:disabled{{opacity:0.5;}}
            """
        return f"""
        QPushButton{{
            background-color:{self.c_bg_tertiary};color:{self.c_text_primary};
            border:1px solid {self.c_border};border-radius:5px;
            padding:4px 14px;font-weight:600;font-size:11px;
        }}
        QPushButton:hover{{border-color:{self.c_primary};background-color:{self.c_bg_secondary};}}
        """

    def _slider_style(self) -> str:
        return f"""
        QSlider::groove:horizontal{{background:{self.c_bg_tertiary};height:3px;border-radius:1px;}}
        QSlider::handle:horizontal{{background:{self.c_primary};width:10px;height:10px;margin:-4px 0;border-radius:5px;}}
        QSlider::sub-page:horizontal{{background:{self.c_primary};border-radius:1px;}}
        """

    def _tiny_btn(self) -> str:
        return f"""
        QPushButton{{
            background-color:{self.c_bg_tertiary};color:{self.c_text_primary};
            border:1px solid {self.c_border};border-radius:4px;
            font-size:10px;font-weight:600;padding:0 6px;
        }}
        QPushButton:hover{{border-color:{self.c_primary};background-color:{self.c_bg_secondary};}}
        """
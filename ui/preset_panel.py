import json
from pathlib import Path
from typing import Dict, Any, Optional, Callable

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QCheckBox,
    QSlider, QDoubleSpinBox, QSpinBox, QColorDialog,
    QComboBox
)

DEFAULT_STATIC_PROPERTIES = {
    "rate": {"type": "slider", "text": "FPS", "min": 1, "max": 144, "default": 60},
    "alignment": {"type": "combo", "text": "Alignment", "default": 0,
                  "options": ["Center", "Left", "Right", "Top", "Bottom"]},
    "alignmentfliph": {"type": "bool", "text": "Flip Horizontal", "default": False},
    "alignmentx": {"type": "slider", "text": "X Offset", "min": 0, "max": 100, "default": 50},
    "alignmenty": {"type": "slider", "text": "Y Offset", "min": 0, "max": 100, "default": 50},
    "alignmentz": {"type": "slider", "text": "Zoom", "min": 0, "max": 200, "default": 100},
    "wec_brs": {"type": "slider", "text": "Brightness", "min": 0, "max": 100, "default": 50},
    "wec_con": {"type": "slider", "text": "Contrast", "min": 0, "max": 100, "default": 50},
    "wec_sa": {"type": "slider", "text": "Saturation", "min": 0, "max": 100, "default": 50},
    "wec_hue": {"type": "slider", "text": "Hue", "min": 0, "max": 100, "default": 50},
}

class PropertyWidget(QWidget):

    value_changed = pyqtSignal(str, object)

    def __init__(self, key: str, prop_data: dict, on_change: Callable, parent=None):
        super().__init__(parent)
        self.key = key
        self.prop_data = prop_data
        self.on_change = on_change
        self.condition = prop_data.get("condition")

        self._is_float = False
        self._updating = False

        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 4, 5, 4)
        layout.setSpacing(8)

        if self.condition:
            spacer = QWidget()
            spacer.setFixedWidth(12)
            spacer.setStyleSheet("background: transparent;")
            layout.addWidget(spacer)

        prop_type = self.prop_data.get("type", "bool")
        text = self.prop_data.get("text", self.key)
        value = self.prop_data.get("value")

        if prop_type == "bool":
            self._create_bool_widget(layout, text, value)
        elif prop_type == "slider":
            self._create_slider_widget(layout, text, value)
        elif prop_type == "color":
            self._create_color_widget(layout, text, value)
        elif prop_type == "combo":
            self._create_combo_widget(layout, text, value)
        else:
            label = QLabel(f"{text}: {value}")
            label.setStyleSheet("color: #a3a3a3; font-size: 13px;")
            layout.addWidget(label)

        self.setStyleSheet("background: transparent; border: none;")

    def set_value(self, value, emit_signal: bool = False):
        if self._updating:
            return
        self._updating = True
        try:
            prop_type = self.prop_data.get("type", "bool")
            if prop_type == "bool" and hasattr(self, 'checkbox'):
                self.checkbox.setChecked(bool(value))
            elif prop_type == "slider" and hasattr(self, 'spinbox'):
                if self._is_float:
                    self.spinbox.setValue(float(value))
                else:
                    self.spinbox.setValue(int(value))
            elif prop_type == "color" and hasattr(self, 'color_btn'):
                try:
                    parts = str(value).split()
                    self._color = QColor(int(float(parts[0]) * 255), int(float(parts[1]) * 255), int(float(parts[2]) * 255))
                    self._update_color_button()
                except:
                    pass
            elif prop_type == "combo" and hasattr(self, 'combo'):
                if isinstance(value, int):
                    self.combo.setCurrentIndex(value)
        finally:
            self._updating = False
        if emit_signal:
            self.value_changed.emit(self.key, value)

    def get_value(self):
        prop_type = self.prop_data.get("type", "bool")
        if prop_type == "bool":
            return self.checkbox.isChecked()
        elif prop_type == "slider":
            return self.spinbox.value()
        elif prop_type == "color":
            return f"{self._color.redF():.5f} {self._color.greenF():.5f} {self._color.blueF():.5f}"
        elif prop_type == "combo":
            return self.combo.currentIndex()
        return self.prop_data.get("value")

    def _create_bool_widget(self, layout, text, value):
        self.checkbox = QCheckBox(text)
        self.checkbox.setChecked(bool(value) if value is not None else False)
        self.checkbox.setStyleSheet("""
            QCheckBox { color: #dcdcdc; font-size: 13px; spacing: 8px; background: transparent; }
            QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #3c3f58; background: #2c2f48; }
            QCheckBox::indicator:checked { background-color: #4e8cff; border: 2px solid #4e8cff; }
            QCheckBox::indicator:hover { border: 2px solid #4e8cff; }
        """)
        self.checkbox.stateChanged.connect(self._on_bool_changed)
        layout.addWidget(self.checkbox)
        layout.addStretch()

    def _create_slider_widget(self, layout, text, value):
        container = QVBoxLayout()
        container.setSpacing(4)
        container.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        header.setSpacing(10)
        label = QLabel(text)
        label.setStyleSheet("color: #dcdcdc; font-size: 13px; background: transparent;")
        header.addWidget(label)
        header.addStretch()

        min_val = self.prop_data.get("min", 0)
        max_val = self.prop_data.get("max", 100)
        step = self.prop_data.get("step", 1)
        precision = self.prop_data.get("precision", 0)
        is_fraction = self.prop_data.get("fraction", False)
        self._is_float = is_fraction or precision > 0 or (isinstance(step, float) and step < 1)

        if self._is_float:
            self.spinbox = QDoubleSpinBox()
            self.spinbox.setRange(float(min_val), float(max_val))
            self.spinbox.setSingleStep(float(step) if step else 0.1)
            self.spinbox.setDecimals(precision if precision > 0 else 2)
            self.spinbox.setValue(float(value) if value is not None else 0.0)
            self._multiplier = 10 ** (precision if precision > 0 else 2)
        else:
            self.spinbox = QSpinBox()
            self.spinbox.setRange(int(min_val), int(max_val))
            self.spinbox.setSingleStep(max(1, int(step)))
            self.spinbox.setValue(int(value) if value is not None else 0)
            self._multiplier = 1

        self.spinbox.setFixedWidth(65)
        self.spinbox.setStyleSheet("""
            QSpinBox, QDoubleSpinBox { background-color: #2c2f48; color: white; border: 1px solid #3c3f58; border-radius: 6px; padding: 3px 6px; font-size: 12px; }
            QSpinBox::up-button, QDoubleSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::down-button { width: 14px; background: #3c3f58; border: none; border-radius: 2px; }
            QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover, QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover { background: #4e8cff; }
        """)
        header.addWidget(self.spinbox)
        container.addLayout(header)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(int(min_val * self._multiplier), int(max_val * self._multiplier))
        self.slider.setValue(int(float(value if value is not None else 0) * self._multiplier))
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal { height: 6px; background: #2c2f48; border-radius: 3px; }
            QSlider::handle:horizontal { width: 16px; height: 16px; margin: -5px 0; background: #4e8cff; border-radius: 8px; }
            QSlider::handle:horizontal:hover { background: #6ea4ff; }
            QSlider::sub-page:horizontal { background: #4e8cff; border-radius: 3px; }
        """)
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)
        container.addWidget(self.slider)

        wrapper = QWidget()
        wrapper.setLayout(container)
        wrapper.setStyleSheet("background: transparent;")
        layout.addWidget(wrapper)

    def _create_color_widget(self, layout, text, value):
        label = QLabel(text)
        label.setStyleSheet("color: #dcdcdc; font-size: 13px; background: transparent;")
        layout.addWidget(label)
        layout.addStretch()
        try:
            parts = str(value).split()
            self._color = QColor(int(float(parts[0]) * 255), int(float(parts[1]) * 255), int(float(parts[2]) * 255))
        except:
            self._color = QColor(255, 255, 255)
        self.color_btn = QPushButton()
        self.color_btn.setFixedSize(60, 26)
        self._update_color_button()
        self.color_btn.clicked.connect(self._on_color_clicked)
        layout.addWidget(self.color_btn)

    def _create_combo_widget(self, layout, text, value):
        label = QLabel(text)
        label.setStyleSheet("color: #dcdcdc; font-size: 13px; background: transparent;")
        layout.addWidget(label)
        layout.addStretch()
        self.combo = QComboBox()
        options = self.prop_data.get("options", [])
        self.combo.addItems(options)
        if isinstance(value, int) and 0 <= value < len(options):
            self.combo.setCurrentIndex(value)
        self.combo.setFixedWidth(100)
        self.combo.setStyleSheet("""
            QComboBox { background-color: #2c2f48; color: white; border: 1px solid #3c3f58; border-radius: 6px; padding: 4px 10px; font-size: 12px; }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid #a3a3a3; margin-right: 8px; }
            QComboBox QAbstractItemView { background-color: #2c2f48; color: white; selection-background-color: #4e8cff; border: 1px solid #3c3f58; }
        """)
        self.combo.currentIndexChanged.connect(self._on_combo_changed)
        layout.addWidget(self.combo)

    def _update_color_button(self):
        self.color_btn.setStyleSheet(
            f"QPushButton {{ background-color: {self._color.name()}; border: 2px solid #3c3f58; border-radius: 6px; }}"
            f" QPushButton:hover {{ border: 2px solid #4e8cff; }}"
        )

    def _on_bool_changed(self, state):
        if self._updating:
            return
        value = state == Qt.CheckState.Checked.value
        self.value_changed.emit(self.key, value)
        self.on_change(self.key, value)

    def _on_slider_changed(self, slider_value):
        if self._updating:
            return
        real_value = slider_value / self._multiplier if self._is_float else slider_value
        self._updating = True
        self.spinbox.setValue(float(real_value) if self._is_float else int(real_value))
        self._updating = False
        self.value_changed.emit(self.key, real_value)
        self.on_change(self.key, real_value)

    def _on_spinbox_changed(self, spinbox_value):
        if self._updating:
            return
        self._updating = True
        self.slider.setValue(int(float(spinbox_value) * self._multiplier) if self._is_float else int(spinbox_value))
        self._updating = False
        self.value_changed.emit(self.key, spinbox_value)
        self.on_change(self.key, spinbox_value)

    def _on_color_clicked(self):
        color = QColorDialog.getColor(self._color, self, "Select Color")
        if color.isValid():
            self._color = color
            self._update_color_button()
            value = f"{color.redF():.5f} {color.greenF():.5f} {color.blueF():.5f}"
            self.value_changed.emit(self.key, value)
            self.on_change(self.key, value)

    def _on_combo_changed(self, index):
        if self._updating:
            return
        self.value_changed.emit(self.key, index)
        self.on_change(self.key, index)


class PresetPanel(QWidget):

    property_changed = pyqtSignal(str, str, object)
    panel_toggled = pyqtSignal(bool)

    def __init__(self, wallpaper_engine, translator, config_manager=None, parent=None):
        super().__init__(parent)
        self.we = wallpaper_engine
        self.tr = translator

        self.folder_path: Optional[str] = None
        self.pubfileid: Optional[str] = None
        self.project_data: dict = {}
        self._we_file_key: Optional[str] = None
        self._property_widgets: Dict[str, PropertyWidget] = {}
        self._apply_timer: Optional[QTimer] = None
        self._pending_property: Optional[tuple] = None

        self._setup_ui()
        self.setVisible(False)

    def _setup_ui(self):
        self.setObjectName("presetPanel")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        container = QWidget()
        container.setObjectName("presetContainer")
        container.setStyleSheet("#presetContainer { background-color: #1e1e2f; border: 1px solid #3c3f58; border-radius: 8px; }")

        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(12, 10, 12, 10)
        container_layout.setSpacing(10)

        header = QHBoxLayout()
        header.setSpacing(8)
        title = QLabel("⚙️ Preset Settings")
        title.setStyleSheet("font-weight: bold; color: white; font-size: 15px; background: transparent;")
        header.addWidget(title)
        header.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(26, 26)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            "QPushButton { background: #2c2f48; color: #a3a3a3; border: none; border-radius: 13px; font-size: 14px; font-weight: bold; }"
            " QPushButton:hover { background: #ff5c5c; color: white; }"
        )
        close_btn.clicked.connect(self.hide_panel)
        header.addWidget(close_btn)
        container_layout.addLayout(header)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("background-color: #3c3f58;")
        sep.setFixedHeight(1)
        container_layout.addWidget(sep)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollArea > QWidget > QWidget { background: transparent; }
            QScrollBar:vertical { background: #2c2f48; width: 8px; border-radius: 4px; margin: 2px; }
            QScrollBar::handle:vertical { background: #4e8cff; border-radius: 4px; min-height: 30px; }
            QScrollBar::handle:vertical:hover { background: #6ea4ff; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 8, 0, 8)
        self.content_layout.setSpacing(2)

        self.scroll.setWidget(self.content)
        container_layout.addWidget(self.scroll)
        main_layout.addWidget(container)

    def show_panel(self, folder_path: str, project_data: dict):
        self.folder_path = folder_path
        self.pubfileid = Path(folder_path).name if folder_path else None
        self.project_data = project_data
        self._we_file_key = None

        if folder_path:
            project_json = Path(folder_path) / "project.json"
            if project_json.exists():
                self.we.apply_wallpaper(project_json)

        self._build_property_widgets()
        self.setVisible(True)
        self.panel_toggled.emit(True)

    def hide_panel(self):
        self.setVisible(False)
        self._clear_widgets()
        self._we_file_key = None
        self.panel_toggled.emit(False)

    def toggle_panel(self, folder_path: str, project_data: dict):
        if self.isVisible() and self.folder_path == folder_path:
            self.hide_panel()
        else:
            self.show_panel(folder_path, project_data)

    def sync_property(self, pubfileid: str, key: str, value):
        if self.pubfileid == pubfileid and key in self._property_widgets:
            self._property_widgets[key].set_value(value)

    def has_settings(self, project_data: dict) -> bool:
        return True

    def _clear_widgets(self):
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child and child.widget():
                child.widget().deleteLater()
        self._property_widgets.clear()

    def _add_section_header(self, icon: str, text: str, color: str = "#4e8cff"):
        header = QLabel(f"{icon} {text}")
        header.setStyleSheet(f"font-weight: bold; color: {color}; font-size: 13px; background: transparent; padding: 6px 0px 4px 0px;")
        self.content_layout.addWidget(header)

    def _add_separator(self):
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #3c3f58; margin: 8px 0px;")
        self.content_layout.addWidget(sep)

    def _read_we_config(self) -> dict:
        config_path = self.we.config_path
        if not config_path.exists():
            return {}
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[PresetPanel] Error reading WE config: {e}")
            return {}

    def _write_we_config(self, config: dict):
        try:
            with open(self.we.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent="\t", ensure_ascii=False)
            print(f"[PresetPanel] WE config saved")
        except Exception as e:
            print(f"[PresetPanel] Error writing WE config: {e}")

    def _get_we_file_key(self) -> Optional[str]:
        if self._we_file_key:
            return self._we_file_key

        config = self._read_we_config()
        wproperties = config.get("Main", {}).get("wproperties", {})

        if self.pubfileid:
            for file_path in wproperties:
                if f"/{self.pubfileid}/" in file_path or f"\\{self.pubfileid}\\" in file_path:
                    self._we_file_key = file_path
                    return file_path

        selected = (
            config.get("Main", {})
            .get("general", {})
            .get("wallpaperconfig", {})
            .get("selectedwallpapers", {})
        )
        for monitor_key, monitor_info in selected.items():
            file_path = monitor_info.get("file", "")
            if self.pubfileid and f"/{self.pubfileid}/" in file_path:
                self._we_file_key = file_path
                return file_path

        if self.folder_path:
            main_file = self.project_data.get("file", "")
            if main_file:
                constructed = (Path(self.folder_path) / main_file).as_posix()
                self._we_file_key = constructed
                return constructed

        print(f"[PresetPanel] Could not determine file key for {self.pubfileid}")
        return None

    def _load_saved_properties(self) -> Dict[str, Any]:
        file_key = self._get_we_file_key()
        if not file_key:
            return {}
        config = self._read_we_config()
        wproperties = config.get("Main", {}).get("wproperties", {})
        saved = wproperties.get(file_key, {}).get("Monitor0", {})
        print(f"[PresetPanel] Loaded {len(saved)} saved properties for {file_key}")
        return saved

    def _save_property_to_we_config(self, key: str, value: Any):
        file_key = self._get_we_file_key()
        if not file_key:
            print(f"[PresetPanel] Cannot save: no file key")
            return

        config = self._read_we_config()
        monitor = (
            config.setdefault("Main", {})
            .setdefault("wproperties", {})
            .setdefault(file_key, {})
            .setdefault("Monitor0", {})
        )
        monitor[key] = value
        self._write_we_config(config)
        print(f"[PresetPanel] Saved to WE config: {key} = {value}")

    def _build_property_widgets(self):
        self._clear_widgets()
        saved_props = self._load_saved_properties()

        properties = self.project_data.get("general", {}).get("properties", {})

        if properties:
            self._add_section_header("📁", "Project Properties")
            sorted_props = sorted(
                properties.items(),
                key=lambda x: x[1].get("order", x[1].get("index", 999))
            )
            for key, prop_data in sorted_props:
                if key == "schemecolor":
                    continue
                prop_with_value = prop_data.copy()
                if key in saved_props:
                    prop_with_value["value"] = saved_props[key]
                widget = PropertyWidget(key, prop_with_value, self._on_property_changed, self.content)
                widget.value_changed.connect(self._emit_property_changed)
                self._property_widgets[key] = widget
                self.content_layout.addWidget(widget)

        self._add_separator()
        self._add_section_header("🌐", "Global Settings", "#9b59b6")

        for key, prop_data in DEFAULT_STATIC_PROPERTIES.items():
            prop_with_value = prop_data.copy()
            prop_with_value["value"] = saved_props.get(key, prop_data.get("default", 0))
            widget = PropertyWidget(key, prop_with_value, self._on_property_changed, self.content)
            widget.value_changed.connect(self._emit_property_changed)
            self._property_widgets[key] = widget
            self.content_layout.addWidget(widget)

        self.content_layout.addStretch()
        self._update_conditional_visibility()

    def _emit_property_changed(self, key: str, value):
        if self.pubfileid:
            self.property_changed.emit(self.pubfileid, key, value)

    def _on_property_changed(self, key: str, value: Any):
        self._update_conditional_visibility()
        self._save_property_to_we_config(key, value)

        self._pending_property = (key, value)
        if self._apply_timer:
            self._apply_timer.stop()
        self._apply_timer = QTimer()
        self._apply_timer.setSingleShot(True)
        self._apply_timer.timeout.connect(self._apply_pending_property)
        self._apply_timer.start(50)

    def _apply_pending_property(self):
        if not self._pending_property:
            return
        key, value = self._pending_property
        self._pending_property = None
        self.we.apply_single_property(key, value)

    def _update_conditional_visibility(self):
        for key, widget in self._property_widgets.items():
            condition = widget.condition
            if condition:
                try:
                    cond_key = condition.split(".")[0]
                    if cond_key in self._property_widgets:
                        widget.setVisible(bool(self._property_widgets[cond_key].get_value()))
                except:
                    widget.setVisible(True)

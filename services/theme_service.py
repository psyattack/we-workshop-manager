from dataclasses import dataclass

from PyQt6.QtWidgets import QApplication


@dataclass
class ThemeDefinition:
    name: str
    colors: dict[str, str]
    stylesheet: str


def _build_stylesheet(colors: dict[str, str]) -> str:
    return f"""
    QWidget {{
        background-color: {colors['bg_primary']};
        color: {colors['text_primary']};
        font-family: 'Segoe UI', 'San Francisco', Arial, sans-serif;
        font-size: 14px;
    }}

    QPushButton {{
        background-color: {colors['primary']};
        color: {colors['text_primary']};
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 14px;
    }}

    QPushButton:hover {{
        background-color: {colors['primary_hover']};
    }}

    QPushButton:pressed {{
        background-color: {colors['primary_pressed']};
    }}

    QPushButton:disabled {{
        background-color: {colors['bg_tertiary']};
        color: {colors['text_disabled']};
    }}

    QLineEdit {{
        padding: 10px 14px;
        border: 2px solid {colors['border']};
        border-radius: 8px;
        background-color: {colors['bg_secondary']};
        color: {colors['text_primary']};
        selection-background-color: {colors['primary']};
        font-size: 14px;
    }}

    QLineEdit:focus {{
        border: 2px solid {colors['primary']};
        background-color: {colors['bg_tertiary']};
    }}

    QComboBox {{
        background-color: {colors['bg_secondary']};
        color: {colors['text_primary']};
        border: 2px solid {colors['border']};
        border-radius: 8px;
        padding: 8px 14px;
        min-height: 32px;
        font-size: 14px;
        font-weight: 500;
    }}

    QComboBox:hover {{
        border: 2px solid {colors['primary']};
        background-color: {colors['bg_tertiary']};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 30px;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 6px solid {colors['text_primary']};
        margin-right: 10px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {colors['bg_elevated']};
        color: {colors['text_primary']};
        selection-background-color: {colors['primary']};
        selection-color: {colors['text_primary']};
        border: 2px solid {colors['border_light']};
        border-radius: 8px;
        outline: none;
        padding: 6px;
    }}

    QComboBox QAbstractItemView::item {{
        min-height: 32px;
        padding: 4px 8px;
        border-radius: 4px;
    }}

    QComboBox QAbstractItemView::item:hover {{
        background-color: {colors['bg_tertiary']};
    }}

    QScrollArea {{
        background-color: transparent;
        border: none;
    }}

    QLabel {{
        background: transparent;
        color: {colors['text_primary']};
    }}

    QMessageBox {{
        background-color: {colors['bg_primary']};
    }}

    QMessageBox QLabel {{
        color: {colors['text_primary']};
    }}

    QMessageBox QPushButton {{
        min-width: 80px;
    }}
    """


class ThemeService:
    def __init__(self):
        self._themes = self._create_themes()
        self.current_theme_name = "dark"
        self.current_theme = self._themes["dark"]

    def _create_themes(self) -> dict[str, ThemeDefinition]:
        raw_themes = {
            "dark": {
                "primary": "#4A7FD9",
                "primary_hover": "#5B8FE9",
                "primary_pressed": "#3A6FC9",
                "bg_primary": "#0F111A",
                "bg_secondary": "#1A1D2E",
                "bg_tertiary": "#252938",
                "bg_elevated": "#2A2F42",
                "text_primary": "#FFFFFF",
                "text_secondary": "#B4B7C3",
                "text_disabled": "#6B6E7C",
                "accent_red": "#EF5B5B",
                "accent_red_hover": "#F57B7B",
                "accent_green": "#5BEF9D",
                "accent_blue": "#4A7FD9",
                "accent_purple": "#9B59D9",
                "border": "#2A2F42",
                "border_light": "#3A3F52",
                "shadow": "rgba(0, 0, 0, 0.4)",
                "shadow_strong": "rgba(0, 0, 0, 0.6)",
                "overlay": "rgba(15, 17, 26, 0.95)",
                "overlay_light": "rgba(26, 29, 46, 0.8)",
            },
            "light": {
                "primary": "#3B82F6",
                "primary_hover": "#2563EB",
                "primary_pressed": "#1D4ED8",
                "bg_primary": "#FFFFFF",
                "bg_secondary": "#F8FAFC",
                "bg_tertiary": "#F1F5F9",
                "bg_elevated": "#E2E8F0",
                "text_primary": "#1E293B",
                "text_secondary": "#64748B",
                "text_disabled": "#94A3B8",
                "accent_red": "#EF4444",
                "accent_red_hover": "#DC2626",
                "accent_green": "#22C55E",
                "accent_blue": "#3B82F6",
                "accent_purple": "#8B5CF6",
                "border": "#E2E8F0",
                "border_light": "#CBD5E1",
                "shadow": "rgba(0, 0, 0, 0.08)",
                "shadow_strong": "rgba(0, 0, 0, 0.15)",
                "overlay": "rgba(255, 255, 255, 0.95)",
                "overlay_light": "rgba(248, 250, 252, 0.8)",
            },
            "nord": {
                "primary": "#88C0D0",
                "primary_hover": "#8FBCBB",
                "primary_pressed": "#5E81AC",
                "bg_primary": "#2E3440",
                "bg_secondary": "#3B4252",
                "bg_tertiary": "#434C5E",
                "bg_elevated": "#4C566A",
                "text_primary": "#ECEFF4",
                "text_secondary": "#D8DEE9",
                "text_disabled": "#6B7B8D",
                "accent_red": "#BF616A",
                "accent_red_hover": "#D08770",
                "accent_green": "#A3BE8C",
                "accent_blue": "#81A1C1",
                "accent_purple": "#B48EAD",
                "border": "#4C566A",
                "border_light": "#5A657A",
                "shadow": "rgba(0, 0, 0, 0.3)",
                "shadow_strong": "rgba(0, 0, 0, 0.5)",
                "overlay": "rgba(46, 52, 64, 0.95)",
                "overlay_light": "rgba(59, 66, 82, 0.8)",
            },
            "monokai": {
                "primary": "#A6E22E",
                "primary_hover": "#B6F23E",
                "primary_pressed": "#86C20E",
                "bg_primary": "#272822",
                "bg_secondary": "#2D2E27",
                "bg_tertiary": "#3E3D32",
                "bg_elevated": "#49483E",
                "text_primary": "#F8F8F2",
                "text_secondary": "#CFCFC2",
                "text_disabled": "#75715E",
                "accent_red": "#F92672",
                "accent_red_hover": "#FF4D8A",
                "accent_green": "#A6E22E",
                "accent_blue": "#66D9EF",
                "accent_purple": "#AE81FF",
                "border": "#49483E",
                "border_light": "#5B5A50",
                "shadow": "rgba(0, 0, 0, 0.4)",
                "shadow_strong": "rgba(0, 0, 0, 0.6)",
                "overlay": "rgba(39, 40, 34, 0.95)",
                "overlay_light": "rgba(62, 61, 50, 0.8)",
            },
            "solarized": {
                "primary": "#268BD2",
                "primary_hover": "#2AA0E8",
                "primary_pressed": "#1A6DA8",
                "bg_primary": "#002B36",
                "bg_secondary": "#073642",
                "bg_tertiary": "#0A3F4E",
                "bg_elevated": "#11505F",
                "text_primary": "#FDF6E3",
                "text_secondary": "#93A1A1",
                "text_disabled": "#586E75",
                "accent_red": "#DC322F",
                "accent_red_hover": "#EC524F",
                "accent_green": "#859900",
                "accent_blue": "#268BD2",
                "accent_purple": "#6C71C4",
                "border": "#11505F",
                "border_light": "#1A6070",
                "shadow": "rgba(0, 0, 0, 0.35)",
                "shadow_strong": "rgba(0, 0, 0, 0.55)",
                "overlay": "rgba(0, 43, 54, 0.95)",
                "overlay_light": "rgba(7, 54, 66, 0.8)",
            },
        }

        result: dict[str, ThemeDefinition] = {}
        for name, colors in raw_themes.items():
            result[name] = ThemeDefinition(
                name=name,
                colors=colors,
                stylesheet=_build_stylesheet(colors),
            )
        return result

    def apply_theme(self, theme_name: str, app: QApplication) -> None:
        if theme_name in self._themes:
            self.current_theme_name = theme_name
            self.current_theme = self._themes[theme_name]
        else:
            self.current_theme_name = "dark"
            self.current_theme = self._themes["dark"]

        app.setStyleSheet(self.current_theme.stylesheet)

    def get_current_theme(self) -> ThemeDefinition:
        return self.current_theme

    def get_color(self, color_name: str) -> str:
        return self.current_theme.colors.get(color_name, "#000000")

    def get_available_themes(self) -> list[str]:
        return list(self._themes.keys())
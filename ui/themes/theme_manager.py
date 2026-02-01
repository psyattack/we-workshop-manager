from PyQt6.QtWidgets import QApplication

class Theme:
    def __init__(self):
        self.colors = {}
        self.stylesheet = ""
    
    def apply(self, app: QApplication):
        app.setStyleSheet(self.stylesheet)

class DarkTheme(Theme):
    def __init__(self):
        super().__init__()
        
        self.colors = {
            'primary': '#4A7FD9',
            'primary_hover': '#5B8FE9',
            'primary_pressed': '#3A6FC9',

            'bg_primary': '#0F111A',
            'bg_secondary': '#1A1D2E',
            'bg_tertiary': '#252938',
            'bg_elevated': '#2A2F42',
            
            'text_primary': '#FFFFFF',
            'text_secondary': '#B4B7C3',
            'text_disabled': '#6B6E7C',
            
            'accent_red': '#EF5B5B',
            'accent_red_hover': '#F57B7B',
            'accent_green': '#5BEF9D',
            'accent_blue': '#4A7FD9',
            'accent_purple': '#9B59D9',
            
            'border': '#2A2F42',
            'border_light': '#3A3F52',
            'shadow': 'rgba(0, 0, 0, 0.4)',
            'shadow_strong': 'rgba(0, 0, 0, 0.6)',

            'overlay': 'rgba(15, 17, 26, 0.95)',
            'overlay_light': 'rgba(26, 29, 46, 0.8)',
        }
        
        self.stylesheet = f"""
            /* === GLOBAL === */
            QWidget {{
                background-color: {self.colors['bg_primary']};
                color: {self.colors['text_primary']};
                font-family: 'Segoe UI', 'San Francisco', Arial, sans-serif;
                font-size: 14px;
            }}
            
            /* === BUTTONS === */
            QPushButton {{
                background-color: {self.colors['primary']};
                color: {self.colors['text_primary']};
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }}
            
            QPushButton:hover {{
                background-color: {self.colors['primary_hover']};
            }}
            
            QPushButton:pressed {{
                background-color: {self.colors['primary_pressed']};
            }}
            
            QPushButton:disabled {{
                background-color: {self.colors['bg_tertiary']};
                color: {self.colors['text_disabled']};
            }}
            
            /* === INPUT FIELDS === */
            QLineEdit {{
                padding: 10px 14px;
                border: 2px solid {self.colors['border']};
                border-radius: 8px;
                background-color: {self.colors['bg_secondary']};
                color: {self.colors['text_primary']};
                selection-background-color: {self.colors['primary']};
                font-size: 14px;
            }}
            
            QLineEdit:focus {{
                border: 2px solid {self.colors['primary']};
                background-color: {self.colors['bg_tertiary']};
            }}
            
            /* === COMBO BOX === */
            QComboBox {{
                background-color: {self.colors['bg_secondary']};
                color: {self.colors['text_primary']};
                border: 2px solid {self.colors['border']};
                border-radius: 8px;
                padding: 8px 14px;
                min-height: 32px;
                font-size: 14px;
                font-weight: 500;
            }}
            
            QComboBox:hover {{
                border: 2px solid {self.colors['primary']};
                background-color: {self.colors['bg_tertiary']};
            }}
            
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {self.colors['text_primary']};
                margin-right: 10px;
            }}
            
            QComboBox QAbstractItemView {{
                background-color: {self.colors['bg_elevated']};
                color: {self.colors['text_primary']};
                selection-background-color: {self.colors['primary']};
                selection-color: {self.colors['text_primary']};
                border: 2px solid {self.colors['border_light']};
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
                background-color: {self.colors['bg_tertiary']};
            }}
            
            /* === SCROLL BARS === */
            QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                margin: 0;
            }}
            
            QScrollBar::handle:vertical {{
                background: {self.colors['primary']};
                min-height: 30px;
                border-radius: 5px;
                margin: 2px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background: {self.colors['primary_hover']};
            }}
            
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            
            QScrollBar:horizontal {{
                background: transparent;
                height: 10px;
                margin: 0;
            }}
            
            QScrollBar::handle:horizontal {{
                background: {self.colors['primary']};
                min-width: 30px;
                border-radius: 5px;
                margin: 2px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background: {self.colors['primary_hover']};
            }}
            
            QScrollBar::add-line:horizontal,
            QScrollBar::sub-line:horizontal {{
                width: 0;
            }}
            
            /* === TABS === */
            QTabBar::tab {{
                background: transparent;
                color: {self.colors['text_secondary']};
                border: 2px solid {self.colors['border']};
                border-radius: 20px;
                padding: 10px 24px;
                margin: 0 4px;
                font-size: 14px;
                font-weight: 600;
                min-width: 100px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {self.colors['primary']};
                color: {self.colors['text_primary']};
                border-color: {self.colors['primary']};
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {self.colors['bg_tertiary']};
                color: {self.colors['text_primary']};
                border-color: {self.colors['primary']};
            }}
            
            /* === SCROLL AREA === */
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            
            /* === LABELS === */
            QLabel {{
                background: transparent;
                color: {self.colors['text_primary']};
            }}
            
            /* === TOOLTIPS === */
            QToolTip {{
                background-color: {self.colors['bg_elevated']};
                color: {self.colors['text_primary']};
                border: 2px solid {self.colors['border_light']};
                padding: 6px 10px;
                border-radius: 6px;
                font-size: 12px;
            }}
            
            /* === MESSAGE BOX === */
            QMessageBox {{
                background-color: {self.colors['bg_primary']};
            }}
            
            QMessageBox QLabel {{
                color: {self.colors['text_primary']};
            }}
            
            QMessageBox QPushButton {{
                min-width: 80px;
            }}
        """

class ThemeManager:
    THEMES = {
        'dark': DarkTheme
    }
    
    def __init__(self):
        self.current_theme_name = 'dark'
        self.current_theme = DarkTheme()
    
    def set_theme(self, theme_name: str, app: QApplication):
        if theme_name in self.THEMES:
            self.current_theme_name = theme_name
            self.current_theme = self.THEMES[theme_name]()
            self.current_theme.apply(app)
    
    def get_current_theme(self) -> Theme:
        return self.current_theme
    
    def get_color(self, color_name: str) -> str:
        return self.current_theme.colors.get(color_name, '#000000')

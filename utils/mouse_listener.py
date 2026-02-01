from PyQt6.QtCore import QThread, pyqtSignal
from pynput.mouse import Listener, Button

class MouseListenerThread(QThread):
    forward_clicked = pyqtSignal()
    back_clicked = pyqtSignal()
    
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self._listener = None
    
    def run(self):
        def on_click(x, y, button, pressed):
            if not pressed or not self.main_window.isActiveWindow():
                return
            
            if button == Button.x2:  # Forward
                self.forward_clicked.emit()
            elif button == Button.x1:  # Back
                self.back_clicked.emit()
        
        with Listener(on_click=on_click) as listener:
            self._listener = listener
            listener.join()
    
    def stop(self):
        if self._listener:
            self._listener.stop()

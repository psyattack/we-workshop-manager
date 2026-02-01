import re
import json
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtCore import pyqtSignal

class CustomWebEnginePage(QWebEnginePage):
    download_requested = pyqtSignal(str, bool)  # pubfileid, go_back
    download_completed = pyqtSignal(str, str, str)  # title, url, pubfileid
    already_installed = pyqtSignal()
    check_status_requested = pyqtSignal(str, str)  # pubfileid, old_text
    
    def __init__(self, profile=None, parent=None):
        if profile is not None:
            super().__init__(profile, parent)
        else:
            super().__init__(parent)
    
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        if message.startswith("CUSTOM_EVENT:") or message.startswith("CUSTOM_EVENT_NOBACK:"):
            go_back = message.startswith("CUSTOM_EVENT:")
            
            if go_back:
                url = message[len("CUSTOM_EVENT:"):]
            else:
                url = message[len("CUSTOM_EVENT_NOBACK:"):]

            pattern = re.search(r'\b\d{8,10}\b', url.strip())
            if pattern:
                pubfileid = pattern.group(0)
                self.download_requested.emit(pubfileid, go_back)
        
        elif message == "ALREADY_INSTALLED":
            self.already_installed.emit()

        elif message.startswith("CHECK_STATUS:"):
            try:
                data = json.loads(message[len("CHECK_STATUS:"):])
                pubfileid = data.get("pubfileid", "")
                text = data.get("text", "")
                self.check_status_requested.emit(pubfileid, text)
            except Exception as e:
                print(f"Failed to parse CHECK_STATUS: {e}")
        
        else:
            super().javaScriptConsoleMessage(level, message, lineNumber, sourceID)

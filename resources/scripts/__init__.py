from pathlib import Path

def load_script(filename: str) -> str:
    script_path = Path(__file__).parent / filename
    
    if not script_path.exists():
        print(f"Script not found: {filename}")
        return ""
    
    try:
        with open(script_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error loading script {filename}: {e}")
        return ""

class WorkshopBrowseScript:
    @staticmethod
    def get_script(bg_url: str) -> str:
        script = load_script("workshop_browse.js")
        if not script:
            return ""

        return f"""
            window.CUSTOM_BG_URL = "{bg_url}";
            {script}
        """

class WorkshopDetailsScript:
    @staticmethod
    def get_script(bg_url: str, custom_event: str, button_text: str) -> str:
        script = load_script("workshop_details.js")
        if not script:
            return ""
        
        return f"""
            window.CUSTOM_BG_URL = "{bg_url}";
            window.CUSTOM_EVENT = "{custom_event}";
            window.BUTTON_TEXT = "{button_text}";
            {script}
        """

class AutoLoginScript:
    @staticmethod
    def get_script(username: str, password: str) -> str:
        script = load_script("auto_login.js")
        if not script:
            return ""
        
        return f"""
            window.STEAM_USERNAME = "{username}";
            window.STEAM_PASSWORD = "{password}";
            {script}
        """

workshop_browse = WorkshopBrowseScript()
workshop_details = WorkshopDetailsScript()
auto_login = AutoLoginScript()

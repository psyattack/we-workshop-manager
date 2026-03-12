import json
from pathlib import Path
from typing import Any


class JsonStorage:
    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)

    def exists(self) -> bool:
        return self.file_path.exists()

    def load(self, default: Any) -> Any:
        if not self.file_path.exists():
            return default

        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                return json.load(file)
        except Exception:
            return default

    def save(self, data: Any) -> bool:
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with self.file_path.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
            return True
        except Exception:
            return False
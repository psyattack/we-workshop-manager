from dataclasses import dataclass
from typing import Optional


@dataclass
class TaskStatus:
    task_id: str
    pid: Optional[int] = None
    status: str = "Starting..."
    account: Optional[str] = None
    output_folder: Optional[str] = None


@dataclass
class DownloadRequest:
    pubfileid: str
    account_index: int


@dataclass
class ExtractionRequest:
    pubfileid: str
    output_directory: str
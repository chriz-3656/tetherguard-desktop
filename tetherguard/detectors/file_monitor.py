import threading
import time
from typing import Optional
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from tetherguard.detectors.base import BaseDetector
from tetherguard.core.events import IncidentEvent, IncidentType, Severity

class SecureFolderHandler(FileSystemEventHandler):
    def __init__(self, callback, device_id):
        self.callback = callback
        self.device_id = device_id
        
    def _trigger(self, event_type, path):
        if self.callback:
            event = IncidentEvent(
                event=IncidentType.FILE_MODIFIED.value,
                device_id=self.device_id,
                severity=Severity.HIGH.value,
                metadata={
                    "path": path,
                    "action": event_type,
                    "threat_level": "Unauthorized Access"
                }
            )
            self.callback(event)

    def on_modified(self, event):
        if not event.is_directory:
            self._trigger("Modified", event.src_path)
            
    def on_created(self, event):
        if not event.is_directory:
            self._trigger("Created", event.src_path)
            
    def on_deleted(self, event):
        if not event.is_directory:
            self._trigger("Deleted", event.src_path)

class FileMonitorDetector(BaseDetector):
    def __init__(self, device_id: str, monitor_path: str = None):
        super().__init__()
        self.device_id = device_id
        # Default to monitoring the user's Documents folder
        self.monitor_path = monitor_path or str(Path.home() / "Documents")
        self.observer = None

    def start(self):
        if self.is_running:
            return
            
        self.is_running = True
        try:
            handler = SecureFolderHandler(self.callback, self.device_id)
            self.observer = Observer()
            self.observer.schedule(handler, self.monitor_path, recursive=False)
            self.observer.start()
            print(f"File Monitor started on: {self.monitor_path}")
        except Exception as e:
            print(f"Failed to start File Monitor: {e}")
            self.is_running = False

    def stop(self):
        self.is_running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()

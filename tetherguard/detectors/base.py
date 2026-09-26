from abc import ABC, abstractmethod
from typing import Callable
from tetherguard.core.events import IncidentEvent

class BaseDetector(ABC):
    def __init__(self):
        self.callback: Callable[[IncidentEvent], None] = None
        self.is_running = False
        
    def set_callback(self, callback: Callable[[IncidentEvent], None]):
        self.callback = callback
        
    @abstractmethod
    def start(self):
        pass
        
    @abstractmethod
    def stop(self):
        pass

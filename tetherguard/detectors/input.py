import threading
import time
from typing import Optional
from tetherguard.detectors.base import BaseDetector
from tetherguard.core.events import IncidentEvent, IncidentType, Severity

class InputDetector(BaseDetector):
    def __init__(self, device_id: str):
        super().__init__()
        self.device_id = device_id
        self.listener = None
        self.last_trigger = 0

    def start(self):
        if self.is_running:
            return
            
        self.is_running = True
        try:
            from pynput import keyboard
            
            def on_press(key):
                if not self.is_running:
                    return False
                    
                # Debounce to prevent flooding alerts for every single keystroke
                current_time = time.time()
                if current_time - self.last_trigger > 5.0:
                    self.last_trigger = current_time
                    self._trigger_alert(str(key))
                    
            self.listener = keyboard.Listener(on_press=on_press)
            self.listener.start()
            print("Input (Keyboard) Monitor started")
        except ImportError:
            print("pynput not installed. Input monitoring disabled.")
            self.is_running = False
        except Exception as e:
            print(f"Failed to start Input Monitor: {e}")
            self.is_running = False

    def _trigger_alert(self, key_str):
        if self.callback:
            event = IncidentEvent(
                event=IncidentType.INPUT_ATTEMPT.value,
                device_id=self.device_id,
                severity=Severity.HIGH.value,
                metadata={
                    "input_type": "KEYBOARD",
                    "key_pressed": key_str,
                    "description": "Unauthorized physical typing detected while armed"
                }
            )
            self.callback(event)

    def stop(self):
        self.is_running = False
        if self.listener:
            self.listener.stop()

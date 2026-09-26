import threading
import time
from typing import Optional
from tetherguard.detectors.base import BaseDetector
from tetherguard.core.events import IncidentEvent, IncidentType, Severity

class WindowsUSBDetector(BaseDetector):
    def __init__(self, device_id: str):
        super().__init__()
        self.device_id = device_id
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self.is_running = True
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()

    def stop(self):
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _monitor(self):
        try:
            import wmi
            c = wmi.WMI()
            # Monitor for __InstanceCreationEvent on Win32_PnPEntity
            watcher = c.watch_for(
                notification_type="Creation",
                wmi_class="Win32_PnPEntity",
                delay_secs=1
            )
            while self.is_running:
                try:
                    usb_event = watcher(timeout_ms=1000)
                    if usb_event:
                        # Only trigger for USB devices or logical disks
                        # Basic filtering for prototype
                        desc = str(getattr(usb_event, "Description", "") or "").upper()
                        if "USB" in desc or "STORAGE" in desc or "DISK" in desc:
                            event = IncidentEvent(
                                event=IncidentType.USB_INSERT.value,
                                device_id=self.device_id,
                                severity=Severity.HIGH.value,
                                metadata={
                                    "device_name": getattr(usb_event, "Name", "Unknown USB Device"),
                                    "device_id": getattr(usb_event, "DeviceID", "Unknown ID"),
                                    "description": getattr(usb_event, "Description", "")
                                }
                            )
                            if self.callback:
                                self.callback(event)
                except wmi.x_wmi_timed_out:
                    continue
                except Exception as e:
                    print(f"USB monitoring error: {e}")
                    time.sleep(1)
        except ImportError:
            print("WMI module not installed. USB detection disabled.")
        except Exception as e:
            print(f"Failed to start USB monitor: {e}")

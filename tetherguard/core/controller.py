import threading
import time
from pathlib import Path
from typing import Callable, Optional
from dataclasses import asdict

from tetherguard.core.events import IncidentEvent, CommandEvent, EventType
from tetherguard.core.config import TetherConfig
from tetherguard.core.guardian import GuardianMode, GuardianState
from tetherguard.storage.database import Database
from tetherguard.communication.websocket import RelayClient
from tetherguard.pairing.auth import AuthManager
from tetherguard.responders.lock import LockResponder
from tetherguard.responders.shutdown import ShutdownResponder
from tetherguard.responders.camera import CameraResponder

class GuardianController:
    def __init__(self, config_path: Path, data_dir: Path):
        self.config_path = config_path
        self.data_dir = data_dir
        self.config = TetherConfig.load(config_path)
        
        self.mode = GuardianMode()
        self.db = Database(data_dir / "incidents.db")
        # We now use the private_key_pem field to store the shared symmetric token
        self.auth = AuthManager(self.config.private_key_pem)
        
        # Responders
        self.lock_resp = LockResponder()
        self.shutdown_resp = ShutdownResponder()
        self.camera_resp = CameraResponder(data_dir / "evidence")
        
        # Communication
        self.relay = RelayClient(self.config.relay_endpoint)
        self.relay.on_command = self.handle_command
        
        # Detectors (initialized later)
        self.detectors = []
        
        # Callbacks for UI
        self.on_state_change: Optional[Callable[[GuardianState], None]] = None
        self.on_incident: Optional[Callable[[IncidentEvent], None]] = None
        self.on_connection_change: Optional[Callable[[bool], None]] = None
        
        # Link relay connection state to controller
        self.relay.on_connection_change = lambda s: self._notify_connection(s)

    def _notify_connection(self, is_connected: bool):
        if self.on_connection_change:
            self.on_connection_change(is_connected)

    def start(self):
        # Generate keys if none exist
        if not self.config.private_key_pem:
            priv, pub = self.auth.generate_keys()
            self.config.private_key_pem = priv
            self.config.public_key_pem = pub
            self.config.save(self.config_path)
            
        self.relay.start()
        
        # Background thread to sync unsent incidents
        threading.Thread(target=self._sync_loop, daemon=True).start()

    def stop(self):
        self.disarm()
        self.relay.stop()

    def arm(self):
        self.mode.arm()
        self._notify_state()
        
        try:
            self._start_detectors()
            self.mode.activate()
            self._notify_state()
        except Exception as e:
            print(f"Failed to arm: {e}")
            self.mode.set_error()
            self._notify_state()

    def disarm(self):
        self.mode.disarm()
        self._notify_state()
        
        self._stop_detectors()
        self.mode.turn_off()
        self._notify_state()

    def _start_detectors(self):
        self.detectors.clear()
        
        if "usb" in self.config.enabled_detectors:
            from tetherguard.detectors.usb import WindowsUSBDetector
            detector = WindowsUSBDetector(self.config.device_id)
            detector.set_callback(self.handle_incident)
            detector.start()
            self.detectors.append(detector)
            
        if "input" in self.config.enabled_detectors:
            from tetherguard.detectors.input import InputDetector
            detector = InputDetector(self.config.device_id)
            detector.set_callback(self.handle_incident)
            detector.start()
            self.detectors.append(detector)
            
        if "file" in self.config.enabled_detectors:
            from tetherguard.detectors.file_monitor import FileMonitorDetector
            detector = FileMonitorDetector(self.config.device_id)
            detector.set_callback(self.handle_incident)
            detector.start()
            self.detectors.append(detector)

    def _stop_detectors(self):
        for detector in self.detectors:
            detector.stop()
        self.detectors.clear()

    def handle_incident(self, event: IncidentEvent):
        # 1. Local incident record
        self.db.save_incident(event)
        
        # Only respond if active
        if self.mode.state == GuardianState.ACTIVE:
            self.mode.trigger()
            self._notify_state()
            
            # 2. Attempt evidence capture
            evidence_b64 = None
            if self.config.evidence_capture_enabled:
                evidence_b64 = self.camera_resp.capture()
                
            # 3. Lock workstation immediately
            self.lock_resp.execute()
            
            # 4. Enqueue to relay
            payload = {
                "event": asdict(event),
                "evidence": evidence_b64
            }
            # Wait for sync loop to send it, or send immediately
            self._send_to_relay(event.incident_id, payload)
            
        if self.on_incident:
            self.on_incident(event)

    def _send_to_relay(self, incident_id: str, payload: dict):
        if self.relay.is_connected and self.config.paired_device_public_key:
            try:
                # Add signature
                sig = self.auth.sign_payload(payload)
                message = {
                    "type": EventType.INCIDENT.value,
                    "device_id": self.config.device_id,
                    "payload": payload,
                    "signature": sig
                }
                self.relay.send_message(message)
                self.db.mark_sent(incident_id)
            except Exception as e:
                print(f"Failed to send incident: {e}")

    def _send_telemetry(self):
        try:
            import psutil
            battery = psutil.sensors_battery()
            battery_pct = battery.percent if battery else 100
        except Exception:
            battery_pct = 100

        from datetime import datetime
        payload = {
            "type": "STATUS",
            "device_id": self.config.device_id,
            "guardian_state": self.mode.state.value,
            "usb_monitoring": "usb" in self.config.enabled_detectors,
            "input_monitoring": False,
            "webcam_watch": self.config.evidence_capture_enabled,
            "lid_sensor": False,
            "workstation_locked": self.mode.state == GuardianState.TRIGGERED,
            "battery_pct": battery_pct,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.relay.send_message(payload)

    def _sync_loop(self):
        while True:
            if self.relay.is_connected:
                # 1. Send Live Telemetry
                self._send_telemetry()
                
                # 2. Sync Unsent Incidents
                unsent = self.db.get_unsent_incidents()
                for incident in unsent:
                    payload = {"event": asdict(incident), "evidence": None} # Skip evidence for backlog?
                    self._send_to_relay(incident.incident_id, payload)
            time.sleep(5)

    def handle_command(self, data: dict):
        if data.get("type") != EventType.COMMAND.value:
            return
            
        if data.get("device_id") != self.config.device_id:
            print(f"Command rejected: Device ID mismatch. Got {data.get('device_id')}, expected {self.config.device_id}")
            return
            
        # Android app sends fields directly at the root
        command = data.get("command", "")
        request_id = data.get("request_id", "")
        timestamp = data.get("timestamp", 0)
        signature = data.get("signature", "")
        
        print(f"\n[DEBUG] Incoming command received: {command}")
        print(f"[DEBUG] Request ID: {request_id} | Timestamp: {timestamp}")
        
        # Verify Signature
        if not self.auth.verify_command_signature(command, self.config.device_id, request_id, timestamp, signature):
            print(f"[ERROR] Invalid HMAC signature on command '{command}'. Rejected.")
            return
            
        print(f"[SUCCESS] Authenticated command verified: {command}")
        
        if command == "LOCK":
            self.lock_resp.execute()
        elif command == "SHUTDOWN":
            self.shutdown_resp.execute()
        elif command == "ARM" or command == "GUARDIAN_ON":
            self.arm()
        elif command == "DISARM" or command == "GUARDIAN_OFF":
            self.disarm()
        elif command == "PING":
            pass # Implement pong if needed

    def _notify_state(self):
        if self.on_state_change:
            self.on_state_change(self.mode.state)

import unittest
import uuid
import json
import base64
from pathlib import Path
from tempfile import TemporaryDirectory

from tetherguard.core.events import IncidentEvent, IncidentType, Severity, CommandEvent
from tetherguard.core.guardian import GuardianMode, GuardianState
from tetherguard.core.controller import GuardianController
from tetherguard.pairing.auth import AuthManager

class TestCoreLogic(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        self.config_path = self.data_dir / "config.json"
        
        self.controller = GuardianController(self.config_path, self.data_dir)
        self.controller.config.device_id = "TG-TEST"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_guardian_state_transitions(self):
        mode = GuardianMode()
        self.assertEqual(mode.state, GuardianState.OFF)
        
        mode.arm()
        self.assertEqual(mode.state, GuardianState.ARMING)
        
        mode.activate()
        self.assertEqual(mode.state, GuardianState.ACTIVE)
        
        mode.trigger()
        self.assertEqual(mode.state, GuardianState.TRIGGERED)
        
        mode.disarm()
        self.assertEqual(mode.state, GuardianState.DISARMING)
        
        mode.turn_off()
        self.assertEqual(mode.state, GuardianState.OFF)

    def test_event_normalization(self):
        ev = IncidentEvent(
            event=IncidentType.USB_INSERT.value,
            device_id="TG-1234",
            severity=Severity.HIGH.value,
            metadata={"device_name": "Test USB"}
        )
        self.assertEqual(ev.type, "INCIDENT")
        self.assertEqual(ev.device_id, "TG-1234")
        self.assertIn("device_name", ev.metadata)
        self.assertTrue(hasattr(ev, "timestamp"))

    def test_command_validation(self):
        # Generate keys for test
        auth = AuthManager()
        priv, pub = auth.generate_keys()
        
        # Set keys in controller
        self.controller.config.private_key_pem = priv
        self.controller.config.public_key_pem = pub
        # Simulate paired device is same as self for test simplicity
        self.controller.config.paired_device_public_key = pub 
        self.controller.auth = auth
        
        payload = {
            "command": "LOCK",
            "device_id": "TG-TEST",
            "request_id": str(uuid.uuid4())
        }
        
        signature = auth.sign_payload(payload)
        
        # Valid command
        valid_cmd = {
            "type": "COMMAND",
            "device_id": "TG-TEST",
            "payload": payload,
            "signature": signature
        }
        
        # Should execute without errors (lock execution might print)
        self.controller.handle_command(valid_cmd)
        
        # Invalid signature
        invalid_cmd = {
            "type": "COMMAND",
            "device_id": "TG-TEST",
            "payload": payload,
            "signature": "invalid_base64_sig"
        }
        # Should not raise, just print error and return
        self.controller.handle_command(invalid_cmd)
        
        # Wrong device ID
        wrong_dev_cmd = {
            "type": "COMMAND",
            "device_id": "TG-OTHER",
            "payload": payload,
            "signature": signature
        }
        self.controller.handle_command(wrong_dev_cmd)

    def test_offline_queue(self):
        ev = IncidentEvent(
            event=IncidentType.INPUT_ACTIVITY.value,
            device_id="TG-TEST",
            severity=Severity.LOW.value,
            metadata={}
        )
        self.controller.db.save_incident(ev)
        
        unsent = self.controller.db.get_unsent_incidents()
        self.assertEqual(len(unsent), 1)
        self.assertEqual(unsent[0].incident_id, ev.incident_id)
        
        self.controller.db.mark_sent(ev.incident_id)
        unsent = self.controller.db.get_unsent_incidents()
        self.assertEqual(len(unsent), 0)

if __name__ == "__main__":
    unittest.main()

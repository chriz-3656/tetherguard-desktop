import enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from typing import Dict, Any, Optional

class EventType(enum.Enum):
    INCIDENT = "INCIDENT"
    COMMAND = "COMMAND"

class IncidentType(enum.Enum):
    USB_INSERT = "USB_INSERT"
    INPUT_ATTEMPT = "INPUT_ATTEMPT"
    FILE_CREATED = "FILE_CREATED"
    FILE_MODIFIED = "FILE_MODIFIED"
    FILE_DELETED = "FILE_DELETED"
    NETWORK_CHANGE = "NETWORK_CHANGE"
    CAMERA_FAILURE = "CAMERA_FAILURE"
    AGENT_ERROR = "AGENT_ERROR"

class Severity(enum.Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

@dataclass
class IncidentEvent:
    event: str
    device_id: str
    severity: str
    metadata: Dict[str, Any]
    type: str = EventType.INCIDENT.value
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    incident_id: str = field(default_factory=lambda: str(uuid.uuid4()))

@dataclass
class CommandEvent:
    command: str
    device_id: str
    request_id: str
    type: str = EventType.COMMAND.value
    payload: Dict[str, Any] = field(default_factory=dict)

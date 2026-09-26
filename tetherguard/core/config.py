import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional

@dataclass
class TetherConfig:
    device_name: str = "TetherGuard-Endpoint"
    device_id: str = ""
    relay_endpoint: str = "ws://localhost:8080/ws"
    paired_device_public_key: str = ""
    enabled_detectors: List[str] = field(default_factory=lambda: ["usb", "input", "file"])
    evidence_capture_enabled: bool = True
    sensitive_directories: List[str] = field(default_factory=list)
    reconnect_interval_sec: int = 5
    retention_days: int = 30
    private_key_pem: str = ""
    public_key_pem: str = ""

    def save(self, path: Path):
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=4)
            
    @classmethod
    def load(cls, path: Path) -> "TetherConfig":
        if not path.exists():
            return cls()
        with open(path, "r") as f:
            data = json.load(f)
            return cls(**data)

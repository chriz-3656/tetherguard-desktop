import sqlite3
from pathlib import Path
import json
from typing import List, Dict, Any
from tetherguard.core.events import IncidentEvent, IncidentType

class Database:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS incidents (
                    incident_id TEXT PRIMARY KEY,
                    event_type TEXT,
                    severity TEXT,
                    timestamp TEXT,
                    metadata TEXT,
                    sent_to_relay INTEGER DEFAULT 0
                )
            ''')
            conn.commit()

    def save_incident(self, incident: IncidentEvent):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO incidents (incident_id, event_type, severity, timestamp, metadata, sent_to_relay)
                VALUES (?, ?, ?, ?, ?, 0)
            ''', (
                incident.incident_id,
                incident.event,
                incident.severity,
                incident.timestamp,
                json.dumps(incident.metadata)
            ))
            conn.commit()

    def mark_sent(self, incident_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('UPDATE incidents SET sent_to_relay = 1 WHERE incident_id = ?', (incident_id,))
            conn.commit()

    def get_unsent_incidents(self) -> List[IncidentEvent]:
        incidents = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT incident_id, event_type, severity, timestamp, metadata FROM incidents WHERE sent_to_relay = 0')
            for row in cursor:
                # We need device_id, maybe store it or pass it. 
                # For prototype, we will just rebuild the event.
                metadata = json.loads(row[4])
                inc = IncidentEvent(
                    incident_id=row[0],
                    event=row[1],
                    severity=row[2],
                    timestamp=row[3],
                    metadata=metadata,
                    device_id=metadata.get("device_id", "unknown")
                )
                incidents.append(inc)
        return incidents

    def get_recent_incidents(self, limit: int = 50) -> List[Dict[str, Any]]:
        incidents = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('SELECT incident_id, event_type, severity, timestamp, sent_to_relay FROM incidents ORDER BY timestamp DESC LIMIT ?', (limit,))
            for row in cursor:
                incidents.append({
                    "incident_id": row[0],
                    "event_type": row[1],
                    "severity": row[2],
                    "timestamp": row[3],
                    "sent": bool(row[4])
                })
        return incidents

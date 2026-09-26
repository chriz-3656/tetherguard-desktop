import sys
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QLabel, QPushButton, QHBoxLayout, QTabWidget, QListWidget, QListWidgetItem, QFrame)
from PySide6.QtCore import Qt, QTimer, Signal, QObject
from PySide6.QtGui import QPixmap, QIcon, QFont

from tetherguard.core.controller import GuardianController
from tetherguard.core.guardian import GuardianState
from tetherguard.core.events import IncidentEvent
from tetherguard.pairing.qr import generate_pairing_qr

class Signals(QObject):
    state_changed = Signal(GuardianState)
    incident_occurred = Signal(object)
    connection_changed = Signal(bool)

class DashboardTab(QWidget):
    def __init__(self, controller: GuardianController, signals: Signals):
        super().__init__()
        self.controller = controller
        
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # Logo
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        logo_path = Path(__file__).parent.parent.parent / "assets" / "logo.jpg"
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            self.logo_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        layout.addWidget(self.logo_label)

        # Title
        title = QLabel("TETHERGUARD")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; letter-spacing: 2px; color: #00d2ff;")
        layout.addWidget(title)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #333;")
        layout.addWidget(line)
        
        # Status
        self.status_label = QLabel("STATUS: OFF")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #888;")
        layout.addWidget(self.status_label)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(20)
        
        self.arm_btn = QPushButton("ARM SYSTEM")
        self.arm_btn.setMinimumHeight(50)
        self.arm_btn.setCursor(Qt.PointingHandCursor)
        self.arm_btn.setStyleSheet("""
            QPushButton {
                background-color: #005c4b; color: white; font-weight: bold; border-radius: 5px; font-size: 16px;
            }
            QPushButton:hover { background-color: #008f75; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.arm_btn.clicked.connect(self.controller.arm)
        
        self.disarm_btn = QPushButton("DISARM")
        self.disarm_btn.setMinimumHeight(50)
        self.disarm_btn.setCursor(Qt.PointingHandCursor)
        self.disarm_btn.setStyleSheet("""
            QPushButton {
                background-color: #8c1c13; color: white; font-weight: bold; border-radius: 5px; font-size: 16px;
            }
            QPushButton:hover { background-color: #b72418; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.disarm_btn.clicked.connect(self.controller.disarm)
        
        btn_layout.addWidget(self.arm_btn)
        btn_layout.addWidget(self.disarm_btn)
        layout.addLayout(btn_layout)
        
        # Last Incident Info
        self.info_panel = QFrame()
        self.info_panel.setStyleSheet("background-color: #1e1e1e; border-radius: 8px; padding: 15px;")
        info_layout = QVBoxLayout(self.info_panel)
        
        self.last_incident_label = QLabel("Last Incident: None")
        self.last_incident_label.setStyleSheet("color: #ccc; font-size: 14px;")
        info_layout.addWidget(self.last_incident_label)
        layout.addWidget(self.info_panel)
        
        # Sync Status
        self.sync_label = QLabel("Sync: OFFLINE")
        self.sync_label.setAlignment(Qt.AlignCenter)
        self.sync_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff3333; margin-top: 10px;")
        layout.addWidget(self.sync_label)
        
        layout.addStretch()
        self.setLayout(layout)
        
        signals.state_changed.connect(self.update_state)
        signals.incident_occurred.connect(self.update_incident)
        signals.connection_changed.connect(self.update_connection)
        
        # Initialize sync state based on controller
        self.update_connection(self.controller.relay.is_connected)

    def update_connection(self, is_connected: bool):
        if is_connected:
            self.sync_label.setText("Sync: CONNECTED")
            self.sync_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #00ffcc; margin-top: 10px;")
        else:
            self.sync_label.setText("Sync: OFFLINE")
            self.sync_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff3333; margin-top: 10px;")

    def update_state(self, state: GuardianState):
        if state == GuardianState.ACTIVE:
            self.status_label.setText("STATUS: ACTIVE")
            self.status_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #00ffcc;")
            self.arm_btn.setEnabled(False)
            self.disarm_btn.setEnabled(True)
        elif state == GuardianState.TRIGGERED:
            self.status_label.setText("STATUS: TRIGGERED")
            self.status_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #ff3333;")
            self.arm_btn.setEnabled(False)
            self.disarm_btn.setEnabled(True)
        elif state == GuardianState.OFF or state == GuardianState.DISARMING:
            self.status_label.setText(f"STATUS: {state.value}")
            self.status_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #888;")
            self.arm_btn.setEnabled(True)
            self.disarm_btn.setEnabled(False)
        else:
            self.status_label.setText(f"STATUS: {state.value}")
            self.status_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #aaa;")

    def update_incident(self, event: IncidentEvent):
        self.last_incident_label.setText(f"Last Incident: <b>{event.event}</b><br>Time: {event.timestamp}")

class IncidentsTab(QWidget):
    def __init__(self, controller: GuardianController, signals: Signals):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        
        title = QLabel("INCIDENT HISTORY")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00d2ff; margin-bottom: 10px;")
        layout.addWidget(title)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet("""
            QListWidget { background-color: #1e1e1e; border: 1px solid #333; border-radius: 5px; padding: 5px; font-size: 14px;}
            QListWidget::item { border-bottom: 1px solid #333; padding: 10px; }
            QListWidget::item:selected { background-color: #2a2a2a; }
        """)
        layout.addWidget(self.list_widget)
        self.setLayout(layout)
        
        signals.incident_occurred.connect(self.add_incident)
        self.load_history()

    def load_history(self):
        incidents = self.controller.db.get_recent_incidents()
        for inc in incidents:
            color = "red" if inc['severity'] == "HIGH" else "yellow"
            item = QListWidgetItem(f"[{inc['timestamp'][:19].replace('T', ' ')}] {inc['event_type']} - Sent: {inc['sent']}")
            self.list_widget.addItem(item)
            
    def add_incident(self, event: IncidentEvent):
        item = QListWidgetItem(f"[{event.timestamp[:19].replace('T', ' ')}] {event.event} - Sent: False")
        self.list_widget.insertItem(0, item)

class SettingsTab(QWidget):
    def __init__(self, controller: GuardianController):
        super().__init__()
        self.controller = controller
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        title = QLabel("DEVICE PAIRING")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #00d2ff;")
        layout.addWidget(title)

        desc = QLabel("Scan this QR code with the TetherGuard mobile app to pair your device.")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #aaa; font-size: 14px;")
        layout.addWidget(desc)

        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setMinimumHeight(220)
        layout.addWidget(self.qr_label)
        
        generate_btn = QPushButton("Generate Pairing QR")
        generate_btn.setMinimumHeight(45)
        generate_btn.setCursor(Qt.PointingHandCursor)
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2b2b2b; color: white; border: 1px solid #444; border-radius: 5px; font-size: 14px;
            }
            QPushButton:hover { background-color: #3b3b3b; }
        """)
        generate_btn.clicked.connect(self.show_qr)
        layout.addWidget(generate_btn)
        
        layout.addStretch()
        self.setLayout(layout)
        
    def show_qr(self):
        qr_path = self.controller.data_dir / "pairing.png"
        generate_pairing_qr(
            self.controller.config.device_id,
            self.controller.config.public_key_pem,
            self.controller.config.relay_endpoint,
            qr_path
        )
        pixmap = QPixmap(str(qr_path))
        self.qr_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))

class MainWindow(QMainWindow):
    def __init__(self, controller: GuardianController):
        super().__init__()
        self.controller = controller
        self.signals = Signals()
        
        self.setWindowTitle("TetherGuard")
        self.resize(500, 650)
        
        # Set Window Icon
        logo_path = Path(__file__).parent.parent.parent / "assets" / "logo.jpg"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))
        
        # Apply dark theme stylesheet globally
        self.setStyleSheet("""
            QMainWindow { background-color: #0f0f0f; color: #ffffff; }
            QWidget { background-color: #0f0f0f; color: #ffffff; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
            QTabWidget::pane { border: 1px solid #333; background-color: #0f0f0f; border-radius: 5px; }
            QTabBar::tab { background-color: #1e1e1e; color: #aaa; padding: 10px 20px; border: 1px solid #333; border-bottom: none; border-top-left-radius: 4px; border-top-right-radius: 4px; font-weight: bold; }
            QTabBar::tab:selected { background-color: #0f0f0f; color: #00d2ff; }
            QTabBar::tab:hover:!selected { background-color: #2a2a2a; }
        """)
        
        self.controller.on_state_change = lambda s: self.signals.state_changed.emit(s)
        self.controller.on_incident = lambda e: self.signals.incident_occurred.emit(e)
        self.controller.on_connection_change = lambda c: self.signals.connection_changed.emit(c)
        
        tabs = QTabWidget()
        tabs.addTab(DashboardTab(controller, self.signals), "Dashboard")
        tabs.addTab(IncidentsTab(controller, self.signals), "History")
        tabs.addTab(SettingsTab(controller), "Pairing")
        
        self.setCentralWidget(tabs)
        
        self.signals.state_changed.emit(self.controller.mode.state)

import sys
import uuid
from pathlib import Path
from PySide6.QtWidgets import QApplication
from tetherguard.core.controller import GuardianController
from tetherguard.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TetherGuard")
    
    # Setup data dir
    data_dir = Path.home() / ".tetherguard"
    data_dir.mkdir(exist_ok=True)
    
    config_path = data_dir / "config.json"
    
    # Initialize controller
    controller = GuardianController(config_path, data_dir)
    
    # Ensure device ID exists
    if not controller.config.device_id:
        controller.config.device_id = f"TG-{str(uuid.uuid4())[:8]}"
        controller.config.save(config_path)
    
    controller.start()
    
    window = MainWindow(controller)
    window.show()
    
    # Mock some data for demo if requested via arguments
    if "--demo" in sys.argv:
        print("Running in demo mode - triggering simulated USB insert in 5 seconds")
        from PySide6.QtCore import QTimer
        from tetherguard.core.events import IncidentEvent, IncidentType, Severity
        def sim_incident():
            if controller.mode.state == getattr(controller.mode.state.__class__, "ACTIVE"):
                ev = IncidentEvent(
                    event=IncidentType.USB_INSERT.value,
                    device_id=controller.config.device_id,
                    severity=Severity.HIGH.value,
                    metadata={"demo": True, "device_name": "Mock Evil USB"}
                )
                controller.handle_incident(ev)
        QTimer.singleShot(5000, sim_incident)
    
    ret = app.exec()
    controller.stop()
    sys.exit(ret)

if __name__ == "__main__":
    main()

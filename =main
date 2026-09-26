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
    
    # Auto-detect local IP so the phone can connect (localhost won't work on the phone)
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        # Update endpoint if it's still using localhost
        if "localhost" in controller.config.relay_endpoint or "127.0.0.1" in controller.config.relay_endpoint:
            controller.config.relay_endpoint = f"ws://{local_ip}:8080"
    except Exception:
        pass

    # Ensure device ID exists
    if not controller.config.device_id:
        controller.config.device_id = f"TG-{str(uuid.uuid4())[:8]}"
        
    # Save config (captures IP change or new ID)
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

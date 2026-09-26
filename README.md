# TetherGuard

TetherGuard is a hackathon-ready physical tamper and endpoint integrity monitoring agent.

## Architecture

TetherGuard is designed with separation of concerns:
- **Detectors**: Monitor OS events (e.g., USB insertion).
- **Responders**: Execute local actions (e.g., Lock workstation, capture camera).
- **Controller**: Coordinates state (Guardian Mode) and responses.
- **Communication**: Handles authenticated WebSocket connection to the relay.
- **Storage**: SQLite database for local incident history and offline queueing.
- **UI**: Lightweight PySide6 interface.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: On Windows, WMI and pywin32 will be installed for USB detection.*

2. Run the application:
   ```bash
   python -m tetherguard.app
   ```

## Demo Mode

To test the full workflow without a real malicious USB device:
```bash
python -m tetherguard.app --demo
```
This will automatically trigger a simulated USB insertion 5 seconds after starting, if Guardian mode is active.

## Security Model

- **Device Identity**: Ed25519 or RSA keypairs are generated per device.
- **Pairing**: Bootstrapped via a QR code containing the device ID, relay endpoint, and public key. No private keys are shared.
- **Authentication**: All remote commands are signed by the paired device and verified locally before execution.
- **Autonomy**: Local response (lock, snapshot) does NOT rely on relay connectivity. Unsent incidents are queued.
- **Privacy**: Camera capture only occurs on explicit incidents, and does not record continuously.

## Windows vs Linux

The primary target for this prototype is **Windows**, utilizing WMI for hardware detection and `user32.dll` for session locking.

### Linux Adapter (Stub)
A partial implementation for Linux exists in the responder logic (`systemctl poweroff` and `loginctl lock-session`).
To fully support Linux:
1. Implement a `LinuxUSBDetector` in `detectors/usb.py` using `pyudev`.
2. Enhance `responders/lock.py` to handle different desktop environments (GNOME, KDE) appropriately.

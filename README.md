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

## ?? Hackathon Challenges & Solutions

During the hackathon, we encountered and solved several complex networking and cryptographic challenges:

1. **Robust QR Pairing (URI Scheme vs JSON):** 
   - *Challenge:* The Android ZXing barcode scanner struggled to reliably decode raw, dense JSON strings off a laptop screen, especially under glare.
   - *Solution:* We migrated from JSON to a custom 	etherguard://pair?... URI scheme. This drastically reduced the QR code density, making camera pairing instantaneous, and allowed native Android URI parsing.

2. **Windows Firewall Network Blocking:**
   - *Challenge:* While the desktop agent connected to the relay server fine on localhost, the Android phone timed out when attempting to connect over the local Wi-Fi. Windows Firewall silently dropped all inbound port 8080 traffic.
   - *Solution:* We decoupled the IP logic. The Desktop Agent natively connects to localhost to bypass the firewall entirely, while dynamically injecting the laptop's external Wi-Fi IP (192.168.x.x) strictly into the QR code. We also built an Administrator ix_firewall.bat script to punch a secure hole for the phone's inbound WebSocket traffic.

3. **Android Cleartext Traffic Block (OS 9+):**
   - *Challenge:* Modern Android OS silently blocks all unencrypted ws:// traffic by default, expecting wss://. This made local Wi-Fi testing impossible.
   - *Solution:* We modified the AndroidManifest.xml to explicitly include ndroid:usesCleartextTraffic="true", allowing seamless peer-to-peer Wi-Fi WebSocket connections without needing a live HTTPS cloud relay for the demo.

4. **Cryptographic Key Mismatch (Asymmetric vs Symmetric):**
   - *Challenge:* The system experienced silent HMAC signature mismatches. The Python desktop agent was inadvertently loading an old RSA Private Key from disk, while the Android phone was hashing with the RSA Public Key from the QR code.
   - *Solution:* We wiped the legacy RSA system and implemented a unified, lightning-fast 32-byte symmetric HMAC-SHA256 token system. Both devices now hash the payload (COMMAND:DEVICE_ID:REQUEST_ID:TIMESTAMP) using the exact same symmetric secret, ensuring mathematical perfection.

5. **Presentation Safe Mode (PySide6 vs Background Threads):**
   - *Challenge:* We needed a way to demonstrate the SHUTDOWN command without actually shutting off the presentation laptop. Attempting to draw a PySide6 GUI warning from a background network thread caused hard crashes due to Qt thread-safety violations.
   - *Solution:* We implemented a native Windows ctypes.windll.user32.MessageBoxW alert in a daemon thread. This perfectly simulates the shutdown intercept with a dramatic, system-modal error dialog that is 100% thread-safe and presentation-friendly.

import qrcode
import json
import base64
from pathlib import Path

def generate_pairing_qr(device_id: str, public_key_pem: str, relay_endpoint: str, output_path: Path):
    """
    Generates a QR code for pairing containing bootstrap data.
    """
    # Use the tetherguard:// URI format which is cleaner and natively supported by the Android app
    # It also produces a less dense QR code making it easier for the camera to scan
    data = f"tetherguard://pair?device_id={device_id}&relay={relay_endpoint}&token={public_key_pem}"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(str(output_path))
    return str(output_path)

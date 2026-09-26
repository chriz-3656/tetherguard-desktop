import qrcode
import json
import base64
from pathlib import Path

def generate_pairing_qr(device_id: str, public_key_pem: str, relay_endpoint: str, output_path: Path):
    """
    Generates a QR code for pairing containing bootstrap data.
    """
    payload = {
        "device_id": device_id,
        "public_key": base64.b64encode(public_key_pem.encode('utf-8')).decode('utf-8'),
        "relay_endpoint": relay_endpoint
    }
    
    data = json.dumps(payload)
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

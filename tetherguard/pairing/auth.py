import json
import base64
import hmac
import hashlib
import secrets

class AuthManager:
    def __init__(self, shared_secret: str = ""):
        self.shared_secret = shared_secret.encode('utf-8') if shared_secret else b""

    def generate_keys(self) -> tuple[str, str]:
        # Generate a secure 32-byte shared secret token instead of RSA
        token = secrets.token_hex(32)
        self.shared_secret = token.encode('utf-8')
        # Return the token for both since there is no public/private split
        return token, token

    def sign_payload(self, payload: dict) -> str:
        if not self.shared_secret:
            raise ValueError("No shared secret available for signing")
            
        message = json.dumps(payload, sort_keys=True).encode('utf-8')
        signature = hmac.new(self.shared_secret, message, hashlib.sha256).digest()
        return base64.b64encode(signature).decode('utf-8')

    def verify_signature(self, payload: dict, signature_b64: str) -> bool:
        try:
            message = json.dumps(payload, sort_keys=True).encode('utf-8')
            signature = base64.b64decode(signature_b64)
            
            expected_signature = hmac.new(self.shared_secret, message, hashlib.sha256).digest()
            return hmac.compare_digest(expected_signature, signature)
        except Exception:
            return False

    def verify_command_signature(self, command: str, device_id: str, request_id: str, timestamp: int, signature_b64: str) -> bool:
        """Verifies an incoming remote command using the Android app's specific string format."""
        try:
            payload_to_sign = f"{command}:{device_id}:{request_id}:{timestamp}".encode('utf-8')
            # Android uses Base64.NO_WRAP to encode the signature
            signature = base64.b64decode(signature_b64)
            expected_signature = hmac.new(self.shared_secret, payload_to_sign, hashlib.sha256).digest()
            
            if hmac.compare_digest(expected_signature, signature):
                return True
            else:
                print(f"[DEBUG HMAC] Signature mismatch.")
                print(f" -> String hashed: {payload_to_sign.decode()}")
                print(f" -> Expected: {base64.b64encode(expected_signature).decode()}")
                print(f" -> Received: {signature_b64}")
                return False
        except Exception as e:
            print(f"[DEBUG HMAC] Exception during verify: {e}")
            return False

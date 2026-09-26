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

    def verify_signature(self, payload: dict, signature_b64: str, peer_public_key_pem: str) -> bool:
        # peer_public_key_pem is effectively the shared secret in this symmetric setup
        try:
            expected_secret = peer_public_key_pem.encode('utf-8')
            message = json.dumps(payload, sort_keys=True).encode('utf-8')
            signature = base64.b64decode(signature_b64)
            
            expected_signature = hmac.new(expected_secret, message, hashlib.sha256).digest()
            return hmac.compare_digest(expected_signature, signature)
        except Exception:
            return False

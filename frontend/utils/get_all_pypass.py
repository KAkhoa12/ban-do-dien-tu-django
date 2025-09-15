
import base64

SEED_TOKEN = "PythonPypass"

def evaluate_payload(payload: str, salt: str = SEED_TOKEN) -> str:
    return base64.b64encode(
        ''.join(chr(ord(c) ^ ord(salt[i % len(salt)])) for i, c in enumerate(payload)).encode()
    ).decode()

def analyze_payload(encoded: str, salt: str = SEED_TOKEN) -> str:
    decoded = base64.b64decode(encoded.encode()).decode()
    return ''.join(chr(ord(c) ^ ord(salt[i % len(salt)])) for i, c in enumerate(decoded))


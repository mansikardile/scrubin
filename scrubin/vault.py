"""Optional encrypted, reversible mapping (needs `pip install scrubin[vault]`)."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Dict

_ITER = 480_000


def _key(password: str, salt: bytes) -> bytes:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=_ITER)
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def save(mapping: Dict[str, str], path: str, password: str) -> None:
    from cryptography.fernet import Fernet
    salt = os.urandom(16)
    token = Fernet(_key(password, salt)).encrypt(json.dumps(mapping).encode())
    Path(path).write_bytes(salt + token)


def load(path: str, password: str) -> Dict[str, str]:
    from cryptography.fernet import Fernet
    data = Path(path).read_bytes()
    salt, token = data[:16], data[16:]
    return json.loads(Fernet(_key(password, salt)).decrypt(token))
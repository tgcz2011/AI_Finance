from __future__ import annotations

import base64
from pathlib import Path

from cryptography.fernet import Fernet


class CryptoManager:
    def __init__(self, key_dir: Path | None = None) -> None:
        if key_dir is None:
            key_dir = Path.home() / ".ai_finance"
        self._key_dir = key_dir
        self._key_path = key_dir / "secret.key"
        self._fernet: Fernet | None = None

    def _ensure_key(self) -> bytes:
        self._key_dir.mkdir(parents=True, exist_ok=True)
        if self._key_path.exists():
            return self._key_path.read_bytes()
        key = Fernet.generate_key()
        self._key_path.write_bytes(key)
        self._key_path.chmod(0o600)
        return key

    def initialize(self) -> None:
        key = self._ensure_key()
        self._fernet = Fernet(key)

    @property
    def is_initialized(self) -> bool:
        return self._fernet is not None

    def encrypt(self, plaintext: str) -> str:
        if self._fernet is None:
            raise RuntimeError("CryptoManager not initialized. Call initialize() first.")
        encrypted = self._fernet.encrypt(plaintext.encode("utf-8"))
        return base64.urlsafe_b64encode(encrypted).decode("ascii")

    def decrypt(self, ciphertext: str) -> str:
        if self._fernet is None:
            raise RuntimeError("CryptoManager not initialized. Call initialize() first.")
        try:
            decoded = base64.urlsafe_b64decode(ciphertext.encode("ascii"))
            decrypted = self._fernet.decrypt(decoded)
            return decrypted.decode("utf-8")
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}") from e

    def rotate_key(self) -> None:
        old_fernet = self._fernet
        new_key = Fernet.generate_key()
        self._key_path.write_bytes(new_key)
        self._key_path.chmod(0o600)
        self._fernet = Fernet(new_key)


import pytest

from src.infrastructure.crypto_.manager import CryptoManager


class TestCryptoManager:
    def test_initialize_creates_key(self, tmp_path):
        mgr = CryptoManager(key_dir=tmp_path)
        mgr.initialize()
        assert mgr.is_initialized
        assert (tmp_path / "secret.key").exists()

    def test_encrypt_decrypt_round_trip(self, tmp_path):
        mgr = CryptoManager(key_dir=tmp_path)
        mgr.initialize()
        plaintext = "sk-1234567890abcdef"
        ciphertext = mgr.encrypt(plaintext)
        assert mgr.decrypt(ciphertext) == plaintext

    def test_ciphertext_is_base64(self, tmp_path):
        mgr = CryptoManager(key_dir=tmp_path)
        mgr.initialize()
        ciphertext = mgr.encrypt("test value")
        import base64
        base64.urlsafe_b64decode(ciphertext.encode("ascii"))

    def test_encrypt_not_initialized_raises(self, tmp_path):
        mgr = CryptoManager(key_dir=tmp_path)
        with pytest.raises(RuntimeError):
            mgr.encrypt("test")

    def test_decrypt_not_initialized_raises(self, tmp_path):
        mgr = CryptoManager(key_dir=tmp_path)
        with pytest.raises(RuntimeError):
            mgr.decrypt("test")

    def test_decrypt_invalid_ciphertext_raises(self, tmp_path):
        mgr = CryptoManager(key_dir=tmp_path)
        mgr.initialize()
        with pytest.raises(ValueError):
            mgr.decrypt("invalid_base64_ciphertext!!!")

    def test_key_file_permissions(self, tmp_path):
        mgr = CryptoManager(key_dir=tmp_path)
        mgr.initialize()
        key_path = tmp_path / "secret.key"
        mode = key_path.stat().st_mode & 0o777
        assert mode == 0o600

    def test_existing_key_reused(self, tmp_path):
        mgr1 = CryptoManager(key_dir=tmp_path)
        mgr1.initialize()
        ciphertext = mgr1.encrypt("hello")
        mgr2 = CryptoManager(key_dir=tmp_path)
        mgr2.initialize()
        assert mgr2.decrypt(ciphertext) == "hello"

    def test_encrypt_empty_string(self, tmp_path):
        mgr = CryptoManager(key_dir=tmp_path)
        mgr.initialize()
        ciphertext = mgr.encrypt("")
        assert mgr.decrypt(ciphertext) == ""

    def test_encrypt_unicode(self, tmp_path):
        mgr = CryptoManager(key_dir=tmp_path)
        mgr.initialize()
        ciphertext = mgr.encrypt("中文API密钥🔑")
        assert mgr.decrypt(ciphertext) == "中文API密钥🔑"

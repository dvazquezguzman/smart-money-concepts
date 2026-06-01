import unittest

from smartmoneyconcepts.dashboard.execution.exchange.encryption import decrypt, encrypt


class TestEncryption(unittest.TestCase):
    def test_roundtrip(self):
        plain = "binance|my-api-key|my-secret-key-123"
        passphrase = "correct-horse-battery-staple"
        encrypted = encrypt(plain, passphrase)
        decrypted = decrypt(encrypted, passphrase)
        self.assertEqual(plain, decrypted)

    def test_different_iv_each_time(self):
        plain = "same-text"
        passphrase = "pass"
        e1 = encrypt(plain, passphrase)
        e2 = encrypt(plain, passphrase)
        self.assertNotEqual(e1, e2)

    def test_wrong_passphrase_fails(self):
        plain = "test-data"
        encrypted = encrypt(plain, "correct-passphrase")
        with self.assertRaises(Exception):
            decrypt(encrypted, "wrong-passphrase")

    def test_empty_string(self):
        encrypted = encrypt("", "pass")
        decrypted = decrypt(encrypted, "pass")
        self.assertEqual(decrypted, "")


if __name__ == "__main__":
    unittest.main()

import os
import base64
from hashlib import pbkdf2_hmac


IV_LENGTH = 12
SALT_LENGTH = 16
KEY_LENGTH = 32
ITERATIONS = 600_000


def _derive_key(passphrase: str, salt: bytes) -> bytes:
    return pbkdf2_hmac(
        "sha256", passphrase.encode(), salt, ITERATIONS, dklen=KEY_LENGTH
    )


def encrypt(plaintext: str, passphrase: str) -> str:
    salt = os.urandom(SALT_LENGTH)
    iv = os.urandom(IV_LENGTH)
    key = _derive_key(passphrase, salt)

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    aes = AESGCM(key)
    ciphertext = aes.encrypt(iv, plaintext.encode(), None)

    combined = salt + iv + ciphertext
    return base64.b64encode(combined).decode()


def decrypt(ciphertext_b64: str, passphrase: str) -> str:
    combined = base64.b64decode(ciphertext_b64)

    salt = combined[:SALT_LENGTH]
    iv = combined[SALT_LENGTH : SALT_LENGTH + IV_LENGTH]
    ciphertext = combined[SALT_LENGTH + IV_LENGTH :]

    key = _derive_key(passphrase, salt)

    from cryptography.hazmat.primitives.ciphers.aead import AESGCM

    aes = AESGCM(key)
    plaintext = aes.decrypt(iv, ciphertext, None)
    return plaintext.decode()

"""
encrypt.py - AES-256 encryption for the steganography pipeline.

Uses AES in CBC mode with PKCS7 padding.
The key is derived from a passphrase using SHA-256 so any length passphrase works.
"""

import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad


# AES block size is always 16 bytes
BLOCK_SIZE = AES.block_size  # 16


def derive_key(passphrase: str) -> bytes:
    """Derive a 32-byte (256-bit) AES key from an arbitrary passphrase using SHA-256."""
    return hashlib.sha256(passphrase.encode("utf-8")).digest()


def encrypt_message(message: str, passphrase: str) -> str:
    """
    Encrypt a plaintext message with AES-256-CBC.

    Steps:
        1. Derive 256-bit key from passphrase.
        2. Generate a random 16-byte IV.
        3. Pad the message to a multiple of 16 bytes (PKCS7).
        4. Encrypt with AES-CBC.
        5. Prepend IV to ciphertext and Base64-encode the result.

    Returns:
        Base64-encoded string: IV + ciphertext
    """
    key = derive_key(passphrase)
    iv = get_random_bytes(BLOCK_SIZE)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = pad(message.encode("utf-8"), BLOCK_SIZE)
    ciphertext = cipher.encrypt(padded)
    # Combine IV + ciphertext so the extractor can recover the IV
    combined = iv + ciphertext
    return base64.b64encode(combined).decode("utf-8")


def decrypt_message(b64_payload: str, passphrase: str) -> str:
    """
    Decrypt a Base64-encoded AES-256-CBC payload.

    Steps:
        1. Base64-decode to get IV + ciphertext.
        2. Split out the 16-byte IV.
        3. Decrypt and unpad.

    Returns:
        Original plaintext string.
    """
    key = derive_key(passphrase)
    raw = base64.b64decode(b64_payload.encode("utf-8"))
    iv = raw[:BLOCK_SIZE]
    ciphertext = raw[BLOCK_SIZE:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = cipher.decrypt(ciphertext)
    return unpad(padded, BLOCK_SIZE).decode("utf-8")

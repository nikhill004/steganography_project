"""
decrypt.py - Orchestrates extraction + AES decryption.

This is the high-level counterpart to the embed pipeline in main.py.
It can also be imported directly for programmatic use.
"""

from extract import extract
from encrypt import decrypt_message
from utils import bits_to_text


def decrypt_stego(
    stego_path: str,
    passphrase: str,
    offset_percent: float = 0.0,
    blue_extra: bool = False,
) -> str:
    """
    Full extraction + decryption pipeline.

    Args:
        stego_path:     Path to the stego image.
        passphrase:     AES passphrase used during embedding.
        offset_percent: Must match the value used during embedding.
        blue_extra:     Must match the value used during embedding.

    Returns:
        The original plaintext message.
    """
    # Step 1: Extract raw bits from the stego image
    payload_bits = extract(stego_path, offset_percent=offset_percent, blue_extra=blue_extra)

    # Step 2: Convert bits back to the Base64-encoded AES ciphertext string
    b64_ciphertext = bits_to_text(payload_bits)

    # Step 3: AES-256-CBC decrypt → original plaintext
    plaintext = decrypt_message(b64_ciphertext, passphrase)

    return plaintext

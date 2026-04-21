"""
stego_extract.py - 3-3-2 LSB steganography extraction
Reads the stego image, extracts the hidden bits, reconstructs the
encrypted message, then decrypts it to recover the original plaintext.

Extraction scheme (per pixel):
  Red   channel → extract 3 LSBs
  Green channel → extract 3 LSBs
  Blue  channel → extract 2 LSBs

The first 32 bits encode the payload length (set during embedding).
"""

import numpy as np
from PIL import Image

from utils import binary_to_text
from decrypt import dual_decrypt


# Must match stego_embed.py constants
_R_BITS = 3
_G_BITS = 3
_B_BITS = 2
_BITS_PER_PIXEL = _R_BITS + _G_BITS + _B_BITS   # = 8
_HEADER_BITS = 32


def _extract_bits_from_pixel(r: int, g: int, b: int) -> str:
    """
    Extract 8 hidden bits from one RGB pixel using the 3-3-2 scheme.

    Returns an 8-character binary string: 3 bits (R) + 3 bits (G) + 2 bits (B).
    """
    r_bits = format(r & 0b00000111, f'0{_R_BITS}b')   # 3 LSBs of Red
    g_bits = format(g & 0b00000111, f'0{_G_BITS}b')   # 3 LSBs of Green
    b_bits = format(b & 0b00000011, f'0{_B_BITS}b')   # 2 LSBs of Blue
    return r_bits + g_bits + b_bits


def extract(stego_path: str,
            caesar_shift: int,
            vigenere_key: str) -> str:
    """
    Extract and decrypt the hidden message from a stego image.

    Parameters
    ----------
    stego_path    : str  path to the stego image
    caesar_shift  : int  Caesar Cipher shift used during embedding
    vigenere_key  : str  Vigenere keyword used during embedding

    Returns
    -------
    str  the recovered original plaintext message
    """
    # ------------------------------------------------------------------ #
    # 1. Load stego image
    # ------------------------------------------------------------------ #
    stego_img = Image.open(stego_path).convert("RGB")
    pixels = np.array(stego_img, dtype=np.uint8)
    height, width, _ = pixels.shape
    total_pixels = height * width

    print(f"[Extract] Stego image       : {stego_path}")
    print(f"[Extract] Image size        : {width}×{height} px "
          f"({total_pixels:,} pixels)")

    # ------------------------------------------------------------------ #
    # 2. Read enough pixels to decode the 32-bit header
    # ------------------------------------------------------------------ #
    header_pixels_needed = -(-_HEADER_BITS // _BITS_PER_PIXEL)  # ceiling division
    raw_bits = ""

    for row in range(height):
        for col in range(width):
            r, g, b = int(pixels[row, col, 0]), int(pixels[row, col, 1]), int(pixels[row, col, 2])
            raw_bits += _extract_bits_from_pixel(r, g, b)
            if len(raw_bits) >= _HEADER_BITS:
                break
        if len(raw_bits) >= _HEADER_BITS:
            break

    # Decode header → payload length in bits
    payload_len = int(raw_bits[:_HEADER_BITS], 2)
    print(f"[Extract] Payload bits      : {payload_len}")

    if payload_len == 0:
        raise ValueError("Header indicates 0 payload bits — image may not contain a hidden message.")

    total_bits_needed = _HEADER_BITS + payload_len

    # ------------------------------------------------------------------ #
    # 3. Extract all required bits
    # ------------------------------------------------------------------ #
    # We may already have some bits from the header pass; continue from there.
    pixels_needed = -(-total_bits_needed // _BITS_PER_PIXEL)   # ceiling division

    if pixels_needed > total_pixels:
        raise ValueError(
            f"Payload claims {payload_len} bits but image only holds "
            f"{total_pixels * _BITS_PER_PIXEL - _HEADER_BITS} bits."
        )

    # Re-extract from scratch for clarity (fast enough for typical images)
    all_bits = ""
    for row in range(height):
        for col in range(width):
            r, g, b = int(pixels[row, col, 0]), int(pixels[row, col, 1]), int(pixels[row, col, 2])
            all_bits += _extract_bits_from_pixel(r, g, b)
            if len(all_bits) >= total_bits_needed:
                break
        if len(all_bits) >= total_bits_needed:
            break

    payload_bits = all_bits[_HEADER_BITS: _HEADER_BITS + payload_len]

    # ------------------------------------------------------------------ #
    # 4. Convert binary → ciphertext string
    # ------------------------------------------------------------------ #
    ciphertext = binary_to_text(payload_bits)
    print(f"[Extract] Extracted cipher  : {ciphertext}")

    # ------------------------------------------------------------------ #
    # 5. Dual decrypt: Vigenere → Caesar → plaintext
    # ------------------------------------------------------------------ #
    plaintext = dual_decrypt(ciphertext, caesar_shift, vigenere_key)
    print(f"[Extract] Recovered message : {plaintext}")

    return plaintext

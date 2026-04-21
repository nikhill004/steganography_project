"""
stego_embed.py - 3-3-2 LSB steganography embedding
Hides an encrypted binary payload inside a 24-bit RGB cover image.

Embedding scheme (per pixel):
  Red   channel → 3 LSBs  (bits 0-2)
  Green channel → 3 LSBs  (bits 3-5)
  Blue  channel → 2 LSBs  (bits 6-7)

A 32-bit header (big-endian) is embedded first to store the payload length
in bits, so the extractor knows exactly how many bits to read.
"""

import numpy as np
from PIL import Image

from utils import text_to_binary, set_lsb


# Number of bits stored per channel
_R_BITS = 3
_G_BITS = 3
_B_BITS = 2
_BITS_PER_PIXEL = _R_BITS + _G_BITS + _B_BITS   # = 8

# Header: 32-bit unsigned integer storing payload length in bits
_HEADER_BITS = 32


def _embed_bits_in_pixel(r: int, g: int, b: int,
                          bits: str, offset: int) -> tuple[int, int, int, int]:
    """
    Embed up to 8 bits from *bits* (starting at *offset*) into one RGB pixel.

    Returns (new_r, new_g, new_b, bits_consumed).
    """
    remaining = bits[offset:]
    consumed = 0

    # --- Red: 3 bits ---
    chunk_r = remaining[:_R_BITS].ljust(_R_BITS, '0')
    r = set_lsb(r, chunk_r)
    consumed += min(_R_BITS, len(remaining))
    remaining = remaining[_R_BITS:]

    # --- Green: 3 bits ---
    chunk_g = remaining[:_G_BITS].ljust(_G_BITS, '0')
    g = set_lsb(g, chunk_g)
    consumed += min(_G_BITS, len(remaining))
    remaining = remaining[_G_BITS:]

    # --- Blue: 2 bits ---
    chunk_b = remaining[:_B_BITS].ljust(_B_BITS, '0')
    b = set_lsb(b, chunk_b)
    consumed += min(_B_BITS, len(remaining))

    return r, g, b, consumed


def embed(cover_path: str,
          message: str,
          output_path: str = "stego_image.png") -> np.ndarray:
    """
    Embed *message* (already dual-encrypted) into the cover image.

    Parameters
    ----------
    cover_path  : str  path to the cover image (any format readable by Pillow)
    message     : str  the encrypted message string to hide
    output_path : str  where to save the stego image (default: stego_image.png)

    Returns
    -------
    np.ndarray  the stego image as a NumPy array (H × W × 3, uint8)

    Raises
    ------
    ValueError  if the message is too large for the cover image
    """
    # ------------------------------------------------------------------ #
    # 1. Load cover image and convert to RGB numpy array
    # ------------------------------------------------------------------ #
    cover_img = Image.open(cover_path).convert("RGB")
    pixels = np.array(cover_img, dtype=np.uint8)
    height, width, _ = pixels.shape

    total_pixels = height * width
    max_payload_bits = total_pixels * _BITS_PER_PIXEL - _HEADER_BITS

    # ------------------------------------------------------------------ #
    # 2. Convert message to binary payload
    # ------------------------------------------------------------------ #
    payload_bits = text_to_binary(message)
    payload_len  = len(payload_bits)

    if payload_len > max_payload_bits:
        raise ValueError(
            f"Message too large: needs {payload_len} bits but image can hold "
            f"{max_payload_bits} bits ({max_payload_bits // 8} bytes)."
        )

    # ------------------------------------------------------------------ #
    # 3. Prepend 32-bit header (payload length in bits)
    # ------------------------------------------------------------------ #
    header_bits = format(payload_len, f'0{_HEADER_BITS}b')
    full_bits   = header_bits + payload_bits
    total_bits  = len(full_bits)

    print(f"[Embed] Message length      : {len(message)} characters")
    print(f"[Embed] Payload bits        : {payload_len}")
    print(f"[Embed] Total bits (w/hdr)  : {total_bits}")
    print(f"[Embed] Cover image size    : {width}×{height} px "
          f"({total_pixels:,} pixels)")
    print(f"[Embed] Max capacity        : {max_payload_bits} bits "
          f"({max_payload_bits // 8} bytes)")

    # ------------------------------------------------------------------ #
    # 4. Embed bits pixel by pixel using 3-3-2 scheme
    # ------------------------------------------------------------------ #
    bit_offset = 0
    stego = pixels.copy()

    for row in range(height):
        for col in range(width):
            if bit_offset >= total_bits:
                break

            r, g, b = int(stego[row, col, 0]), int(stego[row, col, 1]), int(stego[row, col, 2])
            r, g, b, _ = _embed_bits_in_pixel(r, g, b, full_bits, bit_offset)
            stego[row, col] = [r, g, b]
            bit_offset += _BITS_PER_PIXEL

        if bit_offset >= total_bits:
            break

    # ------------------------------------------------------------------ #
    # 5. Save stego image as lossless PNG
    # ------------------------------------------------------------------ #
    stego_img = Image.fromarray(stego, mode="RGB")
    stego_img.save(output_path, format="PNG")
    print(f"[Embed] Stego image saved   : {output_path}")

    return stego

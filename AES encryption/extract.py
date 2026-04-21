"""
extract.py - 3-3-2 LSB extraction from a stego image.

Mirrors the embedding process exactly:
    1. Read the first 32 bits (length header) to know payload size.
    2. Read exactly that many payload bits.
    3. Return the raw binary string for the caller to decrypt.
"""

import numpy as np
import cv2

from utils import decode_length_header, compute_offset


def _extract_bits_from_channel(channel_value: int, n: int) -> str:
    """
    Extract the n least significant bits from a channel value.

    Returns:
        Binary string of length n (MSB first within those n bits).
    """
    return format(channel_value & ((1 << n) - 1), f"0{n}b")


def extract(
    stego_path: str,
    offset_percent: float = 0.0,
    blue_extra: bool = False,
) -> str:
    """
    Extract the hidden binary payload from a stego image.

    Args:
        stego_path:     Path to the stego image.
        offset_percent: Must match the value used during embedding.
        blue_extra:     Must match the value used during embedding.

    Returns:
        Binary string of the extracted payload (without the length header).

    Raises:
        FileNotFoundError: If the stego image cannot be loaded.
        ValueError:        If the extracted length header is implausible.
    """
    # ------------------------------------------------------------------ load
    image = cv2.imread(stego_path)
    if image is None:
        raise FileNotFoundError(f"Cannot load stego image: {stego_path}")

    img = image.astype(np.uint8)
    height, width, _ = img.shape
    total_pixels = height * width
    blue_bits = 3 if blue_extra else 2
    bits_per_pixel = 9 if blue_extra else 8

    # --------------------------------------------------------- compute offset
    start_pixel = compute_offset(total_pixels, offset_percent)

    flat = img.reshape(-1, 3)  # B, G, R

    # ------------------------------------------------- phase 1: read header
    # We need 32 bits for the header.  Read enough pixels to cover them.
    header_pixels_needed = -(-32 // bits_per_pixel)  # ceiling division
    raw_bits = []

    for pixel_idx in range(start_pixel, start_pixel + header_pixels_needed):
        b_val = int(flat[pixel_idx, 0])
        g_val = int(flat[pixel_idx, 1])
        r_val = int(flat[pixel_idx, 2])

        raw_bits.append(_extract_bits_from_channel(r_val, 3))   # Red:   3 bits
        raw_bits.append(_extract_bits_from_channel(g_val, 3))   # Green: 3 bits
        raw_bits.append(_extract_bits_from_channel(b_val, blue_bits))  # Blue

    header_stream = "".join(raw_bits)
    payload_length = decode_length_header(header_stream)  # bits

    # Sanity check
    max_possible = (total_pixels - start_pixel) * bits_per_pixel - 32
    if payload_length <= 0 or payload_length > max_possible:
        raise ValueError(
            f"Extracted length header ({payload_length} bits) is out of range. "
            "Check that offset_percent and blue_extra match the embedding parameters."
        )

    # ------------------------------------------- phase 2: read full stream
    total_bits_needed = 32 + payload_length
    total_pixels_needed = -(-total_bits_needed // bits_per_pixel)  # ceiling

    all_bits = []
    for pixel_idx in range(start_pixel, start_pixel + total_pixels_needed):
        b_val = int(flat[pixel_idx, 0])
        g_val = int(flat[pixel_idx, 1])
        r_val = int(flat[pixel_idx, 2])

        all_bits.append(_extract_bits_from_channel(r_val, 3))
        all_bits.append(_extract_bits_from_channel(g_val, 3))
        all_bits.append(_extract_bits_from_channel(b_val, blue_bits))

    full_stream = "".join(all_bits)
    payload_bits = full_stream[32 : 32 + payload_length]

    print(f"[extract] Extracted {payload_length} payload bits "
          f"(offset {offset_percent:.1f}%, blue_extra={blue_extra}).")
    return payload_bits

"""
utils.py - Shared helper utilities.

Provides:
    - text <-> binary string conversion
    - length header encoding / decoding (32-bit big-endian)
    - pixel offset calculation
"""

import struct


def text_to_bits(text: str) -> str:
    """Convert a UTF-8 string to a binary string (e.g. 'A' -> '01000001')."""
    bits = []
    for byte in text.encode("utf-8"):
        bits.append(format(byte, "08b"))
    return "".join(bits)


def bits_to_text(bits: str) -> str:
    """Convert a binary string back to a UTF-8 string."""
    chars = []
    for i in range(0, len(bits), 8):
        byte = bits[i : i + 8]
        if len(byte) < 8:
            break
        chars.append(chr(int(byte, 2)))
    return "".join(chars)


def encode_length_header(length: int) -> str:
    """
    Encode a 32-bit unsigned integer as a 32-character binary string.
    This is prepended to the payload so the extractor knows how many bits to read.
    """
    return format(length, "032b")


def decode_length_header(bits: str) -> int:
    """Decode the first 32 bits of the stream as the payload length (in bits)."""
    return int(bits[:32], 2)


def compute_offset(total_pixels: int, offset_percent: float) -> int:
    """
    Compute the starting pixel index given an offset percentage.

    Args:
        total_pixels:   Total number of pixels in the image.
        offset_percent: Value in [0, 100) indicating how far into the image
                        to start embedding.

    Returns:
        Integer pixel index.
    """
    if not (0.0 <= offset_percent < 100.0):
        raise ValueError("offset_percent must be in [0, 100)")
    return int(total_pixels * offset_percent / 100.0)


def max_payload_bits(total_pixels: int, blue_extra: bool = False) -> int:
    """
    Return the maximum number of payload bits that can be embedded.

    Standard 3-3-2 scheme:  8 bits per pixel.
    Blue-extra scheme:       9 bits per pixel (3-3-3 variant).

    The first 32 bits are always reserved for the length header.
    """
    bits_per_pixel = 9 if blue_extra else 8
    return total_pixels * bits_per_pixel - 32

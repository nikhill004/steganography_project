"""
embed.py - 3-3-2 LSB embedding into a 24-bit RGB image.

Embedding rule (per pixel, 8 bits of secret data):
    Red   channel  <- 3 LSBs replaced  (bits 0-2  of the secret byte)
    Green channel  <- 3 LSBs replaced  (bits 3-5  of the secret byte)
    Blue  channel  <- 2 LSBs replaced  (bits 6-7  of the secret byte)

Optional blue_extra mode uses 3 bits in the Blue channel (3-3-3), giving
9 bits per pixel and ~12.5 % higher payload capacity.

A 32-bit length header is embedded first so the extractor knows exactly
how many payload bits to read.
"""

import numpy as np
import cv2

from utils import text_to_bits, encode_length_header, compute_offset, max_payload_bits


def _embed_bits_in_channel(channel_value: int, bits: str, n: int) -> int:
    """
    Replace the n least significant bits of channel_value with the given bits.

    Args:
        channel_value: Original 8-bit pixel channel value (0-255).
        bits:          Binary string of exactly n characters.
        n:             Number of LSBs to replace (2 or 3).

    Returns:
        Modified channel value.
    """
    # Create a mask that zeroes out the n LSBs, then OR in the new bits
    mask = 0xFF ^ ((1 << n) - 1)          # e.g. n=3 -> 11111000
    new_bits = int(bits, 2)
    return (channel_value & mask) | new_bits


def embed(
    image_path: str,
    payload_bits: str,
    output_path: str,
    offset_percent: float = 0.0,
    blue_extra: bool = False,
) -> np.ndarray:
    """
    Embed payload_bits into the cover image using the 3-3-2 (or 3-3-3) LSB scheme.

    Args:
        image_path:     Path to the cover image (any format OpenCV can read).
        payload_bits:   Binary string of bits to embed (the encrypted message).
        output_path:    Where to save the stego image (PNG recommended).
        offset_percent: Percentage of pixels to skip before starting embedding.
        blue_extra:     If True, use 3 bits in Blue channel instead of 2.

    Returns:
        The stego image as a NumPy array (BGR, uint8).

    Raises:
        ValueError: If the payload is too large for the image.
        FileNotFoundError: If the cover image cannot be loaded.
    """
    # ------------------------------------------------------------------ load
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Cannot load image: {image_path}")

    # OpenCV loads as BGR; we work in-place on the array
    img = image.copy().astype(np.uint8)
    height, width, _ = img.shape
    total_pixels = height * width

    # --------------------------------------------------------- capacity check
    bits_per_pixel = 9 if blue_extra else 8
    blue_bits = 3 if blue_extra else 2

    capacity = max_payload_bits(total_pixels, blue_extra)
    if len(payload_bits) > capacity:
        raise ValueError(
            f"Payload too large: {len(payload_bits)} bits required, "
            f"but image capacity is {capacity} bits "
            f"({total_pixels} pixels × {bits_per_pixel} bits/pixel − 32 header bits)."
        )

    # --------------------------------------------------- build the full stream
    # Prepend a 32-bit header that stores the payload length in bits
    header = encode_length_header(len(payload_bits))
    stream = header + payload_bits

    # --------------------------------------------------------- compute offset
    start_pixel = compute_offset(total_pixels, offset_percent)

    # ----------------------------------------------------------------- embed
    stream_index = 0
    stream_len = len(stream)

    flat = img.reshape(-1, 3)  # shape: (total_pixels, 3)  — channels are B, G, R

    for pixel_idx in range(start_pixel, total_pixels):
        if stream_index >= stream_len:
            break

        # OpenCV stores channels as B, G, R
        b_val = int(flat[pixel_idx, 0])
        g_val = int(flat[pixel_idx, 1])
        r_val = int(flat[pixel_idx, 2])

        # --- Red: 3 bits ---
        if stream_index + 3 <= stream_len:
            r_bits = stream[stream_index : stream_index + 3]
        else:
            r_bits = stream[stream_index:].ljust(3, "0")
        r_val = _embed_bits_in_channel(r_val, r_bits, 3)
        stream_index += 3

        # --- Green: 3 bits ---
        if stream_index < stream_len:
            if stream_index + 3 <= stream_len:
                g_bits = stream[stream_index : stream_index + 3]
            else:
                g_bits = stream[stream_index:].ljust(3, "0")
            g_val = _embed_bits_in_channel(g_val, g_bits, 3)
            stream_index += 3

        # --- Blue: 2 or 3 bits ---
        if stream_index < stream_len:
            if stream_index + blue_bits <= stream_len:
                b_bits = stream[stream_index : stream_index + blue_bits]
            else:
                b_bits = stream[stream_index:].ljust(blue_bits, "0")
            b_val = _embed_bits_in_channel(b_val, b_bits, blue_bits)
            stream_index += blue_bits

        flat[pixel_idx, 0] = b_val
        flat[pixel_idx, 1] = g_val
        flat[pixel_idx, 2] = r_val

    stego = flat.reshape(height, width, 3)
    cv2.imwrite(output_path, stego)
    print(f"[embed] Stego image saved to: {output_path}")
    print(f"[embed] Embedded {len(payload_bits)} payload bits + 32 header bits "
          f"across {stream_len // bits_per_pixel + 1} pixels "
          f"(offset {offset_percent:.1f}%, blue_extra={blue_extra}).")
    return stego

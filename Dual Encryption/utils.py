"""
utils.py - Binary conversion utilities and image metrics
Provides helper functions for bit manipulation, PSNR, MSE, and payload capacity.
"""

import math
import numpy as np


# ---------------------------------------------------------------------------
# Binary / text helpers
# ---------------------------------------------------------------------------

def text_to_binary(text: str) -> str:
    """Convert a string to a concatenated 8-bit binary string."""
    return ''.join(format(ord(ch), '08b') for ch in text)


def binary_to_text(binary: str) -> str:
    """Convert a concatenated 8-bit binary string back to a string."""
    chars = []
    for i in range(0, len(binary), 8):
        byte = binary[i:i + 8]
        if len(byte) < 8:
            break
        chars.append(chr(int(byte, 2)))
    return ''.join(chars)


def int_to_bits(value: int, n: int) -> str:
    """Return the *n* least-significant bits of *value* as a binary string."""
    return format(value & ((1 << n) - 1), f'0{n}b')


def set_lsb(channel_value: int, bits: str) -> int:
    """
    Replace the least-significant len(bits) bits of *channel_value* with *bits*.

    Parameters
    ----------
    channel_value : int  (0-255)
    bits          : str  binary string, e.g. '101'

    Returns
    -------
    int  modified channel value (0-255)
    """
    n = len(bits)
    # Clear the n LSBs then OR in the new bits
    mask = ~((1 << n) - 1) & 0xFF
    return (channel_value & mask) | int(bits, 2)


# ---------------------------------------------------------------------------
# Image quality metrics
# ---------------------------------------------------------------------------

def calculate_mse(original: np.ndarray, stego: np.ndarray) -> float:
    """
    Mean Squared Error between two images.
    Lower is better (0 = identical).
    """
    original = original.astype(np.float64)
    stego = stego.astype(np.float64)
    mse = np.mean((original - stego) ** 2)
    return float(mse)


def calculate_psnr(original: np.ndarray, stego: np.ndarray) -> float:
    """
    Peak Signal-to-Noise Ratio (dB).
    Higher is better; > 40 dB is generally considered imperceptible.
    Returns math.inf when the images are identical.
    """
    mse = calculate_mse(original, stego)
    if mse == 0:
        return math.inf
    max_pixel = 255.0
    psnr = 20 * math.log10(max_pixel / math.sqrt(mse))
    return psnr


def calculate_payload_capacity(image: np.ndarray) -> dict:
    """
    Compute steganographic payload capacity for the 3-3-2 LSB scheme.

    Each pixel stores 3 + 3 + 2 = 8 bits = 1 byte.
    Total capacity = height × width bytes.

    Returns a dict with bits, bytes, and bpp (bits per pixel).
    """
    height, width = image.shape[:2]
    total_pixels = height * width
    bits_per_pixel = 8          # 3 (R) + 3 (G) + 2 (B)
    total_bits = total_pixels * bits_per_pixel
    total_bytes = total_bits // 8

    return {
        "pixels": total_pixels,
        "bits_per_pixel": bits_per_pixel,
        "total_bits": total_bits,
        "total_bytes": total_bytes,
    }


def print_metrics(original: np.ndarray, stego: np.ndarray) -> None:
    """Print a formatted metrics report comparing cover and stego images."""
    mse  = calculate_mse(original, stego)
    psnr = calculate_psnr(original, stego)
    cap  = calculate_payload_capacity(original)

    print("\n" + "=" * 50)
    print("         IMAGE QUALITY METRICS")
    print("=" * 50)
    print(f"  MSE  (Mean Squared Error)  : {mse:.6f}")
    if math.isinf(psnr):
        print(f"  PSNR (Peak SNR)            : ∞ dB  (images identical)")
    else:
        print(f"  PSNR (Peak SNR)            : {psnr:.4f} dB")
    print(f"  Bits per Pixel (BPP)       : {cap['bits_per_pixel']}")
    print(f"  Total Pixels               : {cap['pixels']:,}")
    print(f"  Max Payload Capacity       : {cap['total_bytes']:,} bytes "
          f"({cap['total_bits']:,} bits)")
    print("=" * 50 + "\n")

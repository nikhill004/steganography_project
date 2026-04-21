"""
main.py - Command-line interface for the 3-3-2 LSB Dual-Encryption Steganography tool.

Usage
-----
Embed:
    python main.py embed <cover_image> <message> [options]

Extract:
    python main.py extract <stego_image> [options]

Options:
    --caesar-shift  INT    Caesar Cipher shift value       (default: 3)
    --vigenere-key  STR    Vigenere Cipher keyword         (default: SECRET)
    --output        PATH   Output stego image path         (default: stego_image.png)
    --metrics               Show PSNR / MSE / capacity metrics after embedding

Examples:
    python main.py embed cover.png "HELLO WORLD" --metrics
    python main.py extract stego_image.png
    python main.py embed cover.png "HELLO WORLD" --caesar-shift 5 --vigenere-key MYSECRET --output out.png --metrics
    python main.py extract out.png --caesar-shift 5 --vigenere-key MYSECRET
"""

import argparse
import sys
import os
import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# Local imports
# ---------------------------------------------------------------------------
from encrypt import dual_encrypt
from stego_embed import embed
from stego_extract import extract
from utils import print_metrics, calculate_payload_capacity


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_numpy(path: str) -> np.ndarray:
    """Load an image as a NumPy uint8 array (RGB)."""
    return np.array(Image.open(path).convert("RGB"), dtype=np.uint8)


def _create_sample_cover(path: str = "cover.png",
                          width: int = 512,
                          height: int = 512) -> None:
    """
    Generate a simple gradient cover image for demonstration purposes.
    Only created if the file does not already exist.
    """
    if os.path.exists(path):
        return

    print(f"[Info] '{path}' not found — generating a sample {width}×{height} cover image.")
    img_array = np.zeros((height, width, 3), dtype=np.uint8)

    for row in range(height):
        for col in range(width):
            img_array[row, col, 0] = int((row / height) * 255)          # R gradient
            img_array[row, col, 1] = int((col / width) * 255)           # G gradient
            img_array[row, col, 2] = int(((row + col) / (height + width)) * 255)  # B

    Image.fromarray(img_array, mode="RGB").save(path, format="PNG")
    print(f"[Info] Sample cover image saved as '{path}'.")


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------

def cmd_embed(args: argparse.Namespace) -> None:
    """Handle the 'embed' sub-command."""
    cover_path   = args.cover_image
    message      = args.message
    caesar_shift = args.caesar_shift
    vigenere_key = args.vigenere_key
    output_path  = args.output
    show_metrics = args.metrics

    # Auto-generate cover image if it doesn't exist
    _create_sample_cover(cover_path)

    print("\n" + "=" * 50)
    print("         EMBEDDING PHASE")
    print("=" * 50)
    print(f"  Cover image   : {cover_path}")
    print(f"  Message       : {message}")
    print(f"  Caesar shift  : {caesar_shift}")
    print(f"  Vigenere key  : {vigenere_key}")
    print(f"  Output        : {output_path}")
    print("=" * 50 + "\n")

    # Step 1 – Dual encrypt
    ciphertext = dual_encrypt(message, caesar_shift, vigenere_key)
    print(f"[Encrypt] After Caesar   : {caesar_encrypt_preview(message, caesar_shift)}")
    print(f"[Encrypt] After Vigenere : {ciphertext}\n")

    # Step 2 – Embed into cover image
    stego_array = embed(cover_path, ciphertext, output_path)

    # Step 3 – Optional metrics
    if show_metrics:
        cover_array = _load_numpy(cover_path)
        print_metrics(cover_array, stego_array)

        cap = calculate_payload_capacity(cover_array)
        print(f"  Payload used  : {len(ciphertext)} bytes  "
              f"({len(ciphertext) * 8} bits)")
        print(f"  Capacity used : "
              f"{len(ciphertext) / cap['total_bytes'] * 100:.2f}%\n")

    print("\n[Done] Embedding complete.")


def cmd_extract(args: argparse.Namespace) -> None:
    """Handle the 'extract' sub-command."""
    stego_path   = args.stego_image
    caesar_shift = args.caesar_shift
    vigenere_key = args.vigenere_key

    print("\n" + "=" * 50)
    print("         EXTRACTION PHASE")
    print("=" * 50)
    print(f"  Stego image   : {stego_path}")
    print(f"  Caesar shift  : {caesar_shift}")
    print(f"  Vigenere key  : {vigenere_key}")
    print("=" * 50 + "\n")

    recovered = extract(stego_path, caesar_shift, vigenere_key)

    print("\n" + "=" * 50)
    print(f"  RECOVERED MESSAGE: {recovered}")
    print("=" * 50 + "\n")


def cmd_demo(args: argparse.Namespace) -> None:
    """Run a full embed → extract demo with default parameters."""
    cover_path   = "cover.png"
    stego_path   = "stego_image.png"
    message      = args.message or "HELLO WORLD"
    caesar_shift = args.caesar_shift
    vigenere_key = args.vigenere_key

    _create_sample_cover(cover_path)

    print("\n" + "=" * 60)
    print("   FULL DEMO: Embed + Extract with Dual Encryption")
    print("=" * 60)

    # --- Embed ---
    ciphertext  = dual_encrypt(message, caesar_shift, vigenere_key)
    stego_array = embed(cover_path, ciphertext, stego_path)

    # --- Metrics ---
    cover_array = _load_numpy(cover_path)
    print_metrics(cover_array, stego_array)

    # --- Extract ---
    recovered = extract(stego_path, caesar_shift, vigenere_key)

    print("\n" + "=" * 60)
    print(f"  Original  : {message}")
    print(f"  Recovered : {recovered}")
    print(f"  Match     : {'✓ YES' if message == recovered else '✗ NO'}")
    print("=" * 60 + "\n")


# ---------------------------------------------------------------------------
# Small helper used only for display (avoids circular import)
# ---------------------------------------------------------------------------

def caesar_encrypt_preview(text: str, shift: int) -> str:
    from encrypt import caesar_encrypt
    return caesar_encrypt(text, shift)


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="3-3-2 LSB Steganography with Dual Encryption (Caesar + Vigenere)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--caesar-shift", type=int, default=3,
                        metavar="INT", help="Caesar Cipher shift (default: 3)")
    common.add_argument("--vigenere-key", type=str, default="SECRET",
                        metavar="STR", help="Vigenere keyword (default: SECRET)")

    sub = parser.add_subparsers(dest="command", required=True)

    # embed
    p_embed = sub.add_parser("embed", parents=[common],
                              help="Hide a message inside a cover image")
    p_embed.add_argument("cover_image", help="Path to the cover image")
    p_embed.add_argument("message",     help="Secret message to embed")
    p_embed.add_argument("--output", default="stego_image.png",
                         help="Output stego image path (default: stego_image.png)")
    p_embed.add_argument("--metrics", action="store_true",
                         help="Display PSNR / MSE / capacity metrics")
    p_embed.set_defaults(func=cmd_embed)

    # extract
    p_extract = sub.add_parser("extract", parents=[common],
                                help="Recover a hidden message from a stego image")
    p_extract.add_argument("stego_image", help="Path to the stego image")
    p_extract.set_defaults(func=cmd_extract)

    # demo
    p_demo = sub.add_parser("demo", parents=[common],
                             help="Run a full embed+extract demonstration")
    p_demo.add_argument("--message", default="HELLO WORLD",
                        help="Message to use in the demo (default: 'HELLO WORLD')")
    p_demo.set_defaults(func=cmd_demo)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

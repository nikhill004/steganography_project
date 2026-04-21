"""
main.py - CLI entry point for the AES + 3-3-2 LSB steganography tool.

Usage
-----
Embed:
    python main.py embed <cover_image> <output_image> [options]

Extract:
    python main.py extract <stego_image> [options]

Run with --help for full option details.

Examples
--------
    python main.py embed cover.png stego_image.png \
        --message "HELLO WORLD" --key "securepassword"

    python main.py extract stego_image.png \
        --key "securepassword"

    # With offset and blue-extra options:
    python main.py embed cover.png stego_image.png \
        --message "Secret" --key "mykey" --offset 10.0 --blue-extra

    python main.py extract stego_image.png \
        --key "mykey" --offset 10.0 --blue-extra
"""

import argparse
import sys
import os
import cv2

# ---------------------------------------------------------------------------
# Make sure sibling modules are importable when running from any directory
sys.path.insert(0, os.path.dirname(__file__))

from encrypt import encrypt_message
from embed import embed
from decrypt import decrypt_stego
from metrics import evaluate, print_metrics
from utils import text_to_bits, max_payload_bits


# ─────────────────────────────────────────────────────────────────────────────
# Embed sub-command
# ─────────────────────────────────────────────────────────────────────────────

def cmd_embed(args: argparse.Namespace) -> None:
    """Handle the 'embed' sub-command."""

    # ── 1. Load cover image to check capacity before doing any work ──────────
    cover = cv2.imread(args.cover)
    if cover is None:
        print(f"[error] Cannot load cover image: {args.cover}", file=sys.stderr)
        sys.exit(1)

    h, w, _ = cover.shape
    total_pixels = h * w
    capacity = max_payload_bits(total_pixels, args.blue_extra)
    print(f"[info]  Cover image: {w}×{h} px  ({total_pixels:,} pixels)")
    print(f"[info]  Embedding capacity: {capacity:,} bits  "
          f"({'3-3-3' if args.blue_extra else '3-3-2'} LSB scheme)")

    # ── 2. AES-256 encrypt the message ───────────────────────────────────────
    print("[step 1] Encrypting message with AES-256-CBC …")
    b64_ciphertext = encrypt_message(args.message, args.key)
    print(f"[step 1] Base64 ciphertext ({len(b64_ciphertext)} chars): {b64_ciphertext[:60]}…")

    # ── 3. Convert ciphertext to binary bits ─────────────────────────────────
    print("[step 2] Converting ciphertext to binary …")
    payload_bits = text_to_bits(b64_ciphertext)
    print(f"[step 2] Payload size: {len(payload_bits):,} bits  "
          f"({len(payload_bits)/8:.0f} bytes)")

    if len(payload_bits) > capacity:
        print(
            f"[error] Payload ({len(payload_bits):,} bits) exceeds image capacity "
            f"({capacity:,} bits).  Use a larger image or a shorter message.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── 4. Embed using 3-3-2 (or 3-3-3) LSB ─────────────────────────────────
    print("[step 3] Embedding bits into cover image …")
    stego = embed(
        image_path=args.cover,
        payload_bits=payload_bits,
        output_path=args.output,
        offset_percent=args.offset,
        blue_extra=args.blue_extra,
    )

    # ── 5. Image quality metrics ──────────────────────────────────────────────
    if not args.no_metrics:
        print("[step 4] Computing image quality metrics …")
        metrics = evaluate(cover, stego)
        print_metrics(metrics)

    print(f"[done]  Stego image saved → {args.output}")


# ─────────────────────────────────────────────────────────────────────────────
# Extract sub-command
# ─────────────────────────────────────────────────────────────────────────────

def cmd_extract(args: argparse.Namespace) -> None:
    """Handle the 'extract' sub-command."""

    print("[step 1] Extracting hidden bits from stego image …")
    try:
        plaintext = decrypt_stego(
            stego_path=args.stego,
            passphrase=args.key,
            offset_percent=args.offset,
            blue_extra=args.blue_extra,
        )
    except Exception as exc:
        print(f"[error] Extraction/decryption failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print("\n══════════════════════════════════════")
    print("  Recovered message:")
    print(f"  {plaintext}")
    print("══════════════════════════════════════\n")


# ─────────────────────────────────────────────────────────────────────────────
# Argument parser
# ─────────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="main.py",
        description="AES-256 + 3-3-2 LSB Image Steganography Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── embed ─────────────────────────────────────────────────────────────────
    embed_p = subparsers.add_parser("embed", help="Hide a message inside a cover image.")
    embed_p.add_argument("cover",  help="Path to the cover (carrier) image.")
    embed_p.add_argument("output", help="Path for the output stego image (PNG recommended).")
    embed_p.add_argument("--message", "-m", required=True,
                         help="Secret message to hide.")
    embed_p.add_argument("--key", "-k", required=True,
                         help="AES passphrase (any length; internally hashed to 256 bits).")
    embed_p.add_argument("--offset", "-o", type=float, default=0.0,
                         help="Percentage of pixels to skip before embedding (0–99). Default: 0.")
    embed_p.add_argument("--blue-extra", action="store_true",
                         help="Use 3 bits in Blue channel (3-3-3) for higher capacity.")
    embed_p.add_argument("--no-metrics", action="store_true",
                         help="Skip image quality metric computation.")

    # ── extract ───────────────────────────────────────────────────────────────
    extract_p = subparsers.add_parser("extract", help="Recover a hidden message from a stego image.")
    extract_p.add_argument("stego", help="Path to the stego image.")
    extract_p.add_argument("--key", "-k", required=True,
                           help="AES passphrase used during embedding.")
    extract_p.add_argument("--offset", "-o", type=float, default=0.0,
                           help="Must match the offset used during embedding. Default: 0.")
    extract_p.add_argument("--blue-extra", action="store_true",
                           help="Must match the --blue-extra flag used during embedding.")

    return parser


# ─────────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "embed":
        cmd_embed(args)
    elif args.command == "extract":
        cmd_extract(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

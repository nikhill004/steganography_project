# 3-3-2 LSB Steganography with Dual Encryption

Implementation of the algorithm described in:
> *"Improved Message Payload and Security of Image Steganography using 3-3-2 LSB and Dual Encryption"*

---

## Project Structure

```
steganography_project/
├── main.py            # CLI entry point
├── encrypt.py         # Caesar + Vigenere dual encryption/decryption
├── decrypt.py         # Decryption wrapper (re-exports from encrypt.py)
├── stego_embed.py     # 3-3-2 LSB embedding engine
├── stego_extract.py   # 3-3-2 LSB extraction engine
├── utils.py           # Binary helpers, PSNR, MSE, payload capacity
├── requirements.txt   # Python dependencies
└── README.md          # This file
```

---

## Algorithm Overview

### 1. Dual Encryption

```
Plaintext  →  Caesar Cipher (shift=3)  →  Vigenere Cipher (key="SECRET")  →  Ciphertext
```

**Caesar Cipher** shifts each letter by a fixed amount:
- `H` (shift 3) → `K`
- `HELLO WORLD` → `KHOOR ZRUOG`

**Vigenere Cipher** uses a repeating keyword to shift each letter:
- `KHOOR ZRUOG` + key `SECRET` → `CLQFV SJYQX`

### 2. Binary Conversion

Each character of the ciphertext is converted to its 8-bit ASCII binary representation:
```
C → 01000011
L → 01001100
...
```

### 3. 3-3-2 LSB Embedding (per pixel)

Each 24-bit RGB pixel stores **8 bits** of payload:

```
Secret byte: 1 0 1 0 1 1 0 0
              ↓       ↓     ↓
Red   (3 LSBs): 1 0 1
Green (3 LSBs): 0 1 1
Blue  (2 LSBs): 0 0
```

A 32-bit header is embedded first to record the payload length.

### 4. Extraction & Decryption

Reverse the process:
1. Read 3 LSBs from Red, 3 from Green, 2 from Blue per pixel
2. Reconstruct binary → ciphertext string
3. Vigenere decrypt → Caesar decrypt → original message

---

## Installation

```bash
pip install -r requirements.txt
```

Dependencies: `numpy`, `Pillow`, `opencv-python`

---

## Usage

### Embed a message

```bash
python main.py embed cover.png "HELLO WORLD" --metrics
```

With custom keys:
```bash
python main.py embed cover.png "HELLO WORLD" \
    --caesar-shift 5 \
    --vigenere-key MYSECRET \
    --output out.png \
    --metrics
```

### Extract a message

```bash
python main.py extract stego_image.png
```

With custom keys (must match embedding keys):
```bash
python main.py extract out.png --caesar-shift 5 --vigenere-key MYSECRET
```

### Full demo (auto-generates cover image)

```bash
python main.py demo
python main.py demo --message "MY SECRET TEXT"
```

---

## Options

| Flag | Default | Description |
|------|---------|-------------|
| `--caesar-shift` | `3` | Caesar Cipher shift value |
| `--vigenere-key` | `SECRET` | Vigenere Cipher keyword |
| `--output` | `stego_image.png` | Output stego image path |
| `--metrics` | off | Show PSNR / MSE / capacity after embedding |

---

## Metrics

| Metric | Description | Good value |
|--------|-------------|------------|
| **MSE** | Mean Squared Error between cover and stego | Close to 0 |
| **PSNR** | Peak Signal-to-Noise Ratio (dB) | > 40 dB (imperceptible) |
| **BPP** | Bits per pixel stored | 8 (fixed by 3-3-2 scheme) |
| **Capacity** | Max bytes the image can hold | `height × width` bytes |

Example output for a 512×512 image:
```
MSE  : 0.000184
PSNR : 85.47 dB
BPP  : 8
Max  : 262,144 bytes
```

---

## Example Workflow

```
Input:
  image        = cover.png
  message      = "HELLO WORLD"
  caesar_key   = 3
  vigenere_key = "SECRET"

Encryption steps:
  Caesar   → KHOOR ZRUOG
  Vigenere → CLQFV SJYQX

Embedding:
  Stego image saved as stego_image.png

Extraction:
  python main.py extract stego_image.png

Output:
  HELLO WORLD
```

---

## Notes

- The stego image is always saved as **PNG** (lossless) to prevent bit corruption.
  JPEG compression would destroy the hidden bits.
- The 32-bit header allows messages up to ~2 billion bits in length.
- Non-alphabetic characters (spaces, digits, punctuation) pass through both
  ciphers unchanged, preserving message structure.

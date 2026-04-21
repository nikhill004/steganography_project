# AES-256 + 3-3-2 LSB Image Steganography

Implementation of the algorithms described in:

- *Improved Message Payload and Security of Image Steganography using 3-3-2 LSB*
- *Image Steganography Method using LSB and AES Encryption Algorithm*

---

## How It Works

```
Secret message
      │
      ▼
 AES-256-CBC encrypt  (key derived via SHA-256)
      │
      ▼
 Base64 encode  →  binary string
      │
      ▼
 3-3-2 LSB embed into RGB image
      │
      ▼
 stego_image.png
```

### 3-3-2 Embedding Rule

For every pixel, 8 bits of secret data are hidden:

| Channel | LSBs replaced | Bits from secret byte |
|---------|:-------------:|:---------------------:|
| Red     | 3             | bits 0–2              |
| Green   | 3             | bits 3–5              |
| Blue    | 2             | bits 6–7              |

A 32-bit length header is prepended to the payload so the extractor knows
exactly how many bits to read.

---

## Project Structure

```
steganography_project/
├── main.py                  # CLI entry point
├── encrypt.py               # AES-256-CBC encrypt / decrypt
├── embed.py                 # 3-3-2 LSB embedding
├── extract.py               # 3-3-2 LSB extraction
├── decrypt.py               # High-level extract + decrypt pipeline
├── metrics.py               # MSE, PSNR, SSIM, NCC
├── utils.py                 # Shared helpers (bit conversion, header, offset)
├── generate_test_image.py   # Creates sample cover images
├── requirements.txt
└── README.md
```

---

## Installation

```bash
pip install -r requirements.txt
```

---

## Quick Start

### 1. Generate test cover images

```bash
python generate_test_image.py
# Creates: cover_gradient.png, cover_solid.png, cover_noise.png
```

### 2. Embed a secret message

```bash
python main.py embed cover_gradient.png stego_image.png \
    --message "HELLO WORLD" \
    --key "securepassword"
```

### 3. Extract the message

```bash
python main.py extract stego_image.png \
    --key "securepassword"
```

Expected output:
```
══════════════════════════════════════
  Recovered message:
  HELLO WORLD
══════════════════════════════════════
```

---

## CLI Reference

### `embed`

```
python main.py embed <cover_image> <output_image> [options]

Required:
  cover_image           Path to the cover (carrier) image
  output_image          Path for the stego image (PNG recommended)
  --message / -m        Secret message to hide
  --key / -k            AES passphrase

Optional:
  --offset / -o FLOAT   Skip this % of pixels before embedding (0–99). Default: 0
  --blue-extra          Use 3 bits in Blue channel (3-3-3) for ~12.5% more capacity
  --no-metrics          Skip image quality metric computation
```

### `extract`

```
python main.py extract <stego_image> [options]

Required:
  stego_image           Path to the stego image
  --key / -k            AES passphrase used during embedding

Optional:
  --offset / -o FLOAT   Must match the value used during embedding. Default: 0
  --blue-extra          Must match the flag used during embedding
```

---

## Extra Features

### Offset Embedding

Shift the starting pixel by a percentage of the total image size.
This adds an extra layer of obscurity — an attacker must know the offset
to find the hidden data.

```bash
python main.py embed cover.png stego.png -m "Secret" -k "key" --offset 25.0
python main.py extract stego.png -k "key" --offset 25.0
```

### Blue Channel Optimization (3-3-3 mode)

Use `--blue-extra` to embed 3 bits in the Blue channel instead of 2,
increasing capacity by ~12.5 % at the cost of slightly higher distortion
in the blue channel.

```bash
python main.py embed cover.png stego.png -m "Longer secret" -k "key" --blue-extra
python main.py extract stego.png -k "key" --blue-extra
```

### Image Quality Metrics

Computed automatically after embedding (unless `--no-metrics` is passed):

| Metric | Meaning | Good value |
|--------|---------|------------|
| MSE    | Mean Squared Error | Close to 0 |
| PSNR   | Peak Signal-to-Noise Ratio | > 40 dB |
| SSIM   | Structural Similarity Index | Close to 1 |
| NCC    | Normalized Cross-Correlation | Close to 1 |

---

## Image Capacity

For a 512×512 image (262,144 pixels):

| Mode    | Bits/pixel | Payload capacity |
|---------|:----------:|:----------------:|
| 3-3-2   | 8          | ~256 KB          |
| 3-3-3   | 9          | ~288 KB          |

Note: AES encryption + Base64 encoding expands the message size by ~1.4×,
so a 1,000-character message requires roughly 1,400 bytes of capacity.

---

## Security Notes

- The AES key is derived from the passphrase using SHA-256 (32 bytes / 256 bits).
- A random IV is generated for every encryption, so the same message + key
  produces a different ciphertext each time.
- The IV is prepended to the ciphertext and stored inside the image.
- Without the correct passphrase, the extracted bits are indistinguishable
  from random data.

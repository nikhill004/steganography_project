"""
generate_test_image.py - Creates sample cover images for testing.

Generates:
    cover_gradient.png  - A smooth RGB gradient (good for PSNR testing)
    cover_solid.png     - A solid-colour image
    cover_noise.png     - Random noise image

Run:
    python generate_test_image.py
"""

import numpy as np
import cv2
import os

OUTPUT_DIR = os.path.dirname(__file__)


def gradient_image(width: int = 512, height: int = 512) -> np.ndarray:
    """Create a smooth horizontal RGB gradient."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    for x in range(width):
        r = int(255 * x / width)
        g = int(255 * (width - x) / width)
        b = int(128 + 127 * np.sin(2 * np.pi * x / width))
        img[:, x] = [b, g, r]  # BGR
    return img


def solid_image(width: int = 512, height: int = 512,
                color_bgr=(100, 149, 237)) -> np.ndarray:
    """Create a solid-colour image (default: cornflower blue)."""
    img = np.full((height, width, 3), color_bgr, dtype=np.uint8)
    return img


def noise_image(width: int = 512, height: int = 512) -> np.ndarray:
    """Create a random-noise image."""
    rng = np.random.default_rng(seed=42)
    return rng.integers(0, 256, (height, width, 3), dtype=np.uint8)


def main():
    images = {
        "cover_gradient.png": gradient_image(),
        "cover_solid.png":    solid_image(),
        "cover_noise.png":    noise_image(),
    }
    for filename, img in images.items():
        path = os.path.join(OUTPUT_DIR, filename)
        cv2.imwrite(path, img)
        h, w = img.shape[:2]
        print(f"Created {path}  ({w}×{h} px, capacity ≈ {w*h*8//8} bytes payload)")


if __name__ == "__main__":
    main()

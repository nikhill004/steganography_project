"""
metrics.py - Image quality evaluation metrics.

Implements:
    MSE   - Mean Squared Error
    PSNR  - Peak Signal-to-Noise Ratio
    SSIM  - Structural Similarity Index
    NCC   - Normalized Cross-Correlation

All functions accept NumPy arrays (uint8, shape H×W×3) as returned by
cv2.imread().  Images must have the same shape.
"""

import numpy as np
import cv2
from skimage.metrics import structural_similarity as ssim_skimage


def mse(original: np.ndarray, stego: np.ndarray) -> float:
    """
    Mean Squared Error between two images.

    MSE = (1 / N) * Σ (original_i - stego_i)²

    A lower MSE means the stego image is closer to the original.
    MSE = 0 means the images are identical.
    """
    orig = original.astype(np.float64)
    stg = stego.astype(np.float64)
    return float(np.mean((orig - stg) ** 2))


def psnr(original: np.ndarray, stego: np.ndarray) -> float:
    """
    Peak Signal-to-Noise Ratio (dB).

    PSNR = 10 * log10(MAX² / MSE)

    For 8-bit images MAX = 255.
    Higher PSNR → better quality (less distortion).
    PSNR > 40 dB is generally considered imperceptible to the human eye.
    Returns inf if MSE == 0 (identical images).
    """
    error = mse(original, stego)
    if error == 0:
        return float("inf")
    max_pixel = 255.0
    return float(10.0 * np.log10((max_pixel ** 2) / error))


def ssim(original: np.ndarray, stego: np.ndarray) -> float:
    """
    Structural Similarity Index (SSIM).

    Measures perceived quality by comparing luminance, contrast, and structure.
    Range: [-1, 1].  A value of 1 means the images are identical.
    Values > 0.95 are typically considered high quality.
    """
    # skimage expects channel_axis for colour images
    score, _ = ssim_skimage(
        original,
        stego,
        channel_axis=2,
        data_range=255,
        full=True,
    )
    return float(score)


def ncc(original: np.ndarray, stego: np.ndarray) -> float:
    """
    Normalized Cross-Correlation (NCC).

    NCC = Σ(orig * stego) / sqrt(Σ orig² * Σ stego²)

    Range: [-1, 1].  A value of 1 means perfect positive correlation.
    Values close to 1 indicate the stego image is visually similar to the original.
    """
    orig = original.astype(np.float64).ravel()
    stg = stego.astype(np.float64).ravel()
    numerator = np.dot(orig, stg)
    denominator = np.sqrt(np.dot(orig, orig) * np.dot(stg, stg))
    if denominator == 0:
        return 0.0
    return float(numerator / denominator)


def evaluate(original: np.ndarray, stego: np.ndarray) -> dict:
    """
    Compute all four metrics and return them as a dictionary.

    Args:
        original: Cover image (NumPy array, uint8, BGR).
        stego:    Stego image (NumPy array, uint8, BGR).

    Returns:
        Dict with keys: mse, psnr, ssim, ncc.
    """
    if original.shape != stego.shape:
        raise ValueError(
            f"Image shapes differ: original {original.shape} vs stego {stego.shape}"
        )
    results = {
        "mse":  mse(original, stego),
        "psnr": psnr(original, stego),
        "ssim": ssim(original, stego),
        "ncc":  ncc(original, stego),
    }
    return results


def print_metrics(metrics: dict) -> None:
    """Pretty-print the metrics dictionary."""
    print("\n── Image Quality Metrics ──────────────────────")
    print(f"  MSE  : {metrics['mse']:.6f}  (lower is better, 0 = identical)")
    print(f"  PSNR : {metrics['psnr']:.4f} dB  (higher is better, >40 dB = imperceptible)")
    print(f"  SSIM : {metrics['ssim']:.6f}  (higher is better, 1 = identical)")
    print(f"  NCC  : {metrics['ncc']:.6f}  (higher is better, 1 = perfect correlation)")
    print("───────────────────────────────────────────────\n")

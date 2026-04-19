import numpy as np
import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.fft import fft2, fftshift
from config import FFT_LOW_CUTOFF, FFT_MID_CUTOFF


def generate_visualizations(
    processed: dict, residuals: dict, features: dict, out_dir: Path
) -> None:
    out_dir = Path(out_dir)
    _save_residuals(residuals, out_dir)
    _save_spectrum(processed, out_dir)
    _save_heatmap(features, out_dir)
    _save_channel_noise(residuals, out_dir)


# ---------------------------------------------------------------------------
# Residual panel
# ---------------------------------------------------------------------------

def _save_residuals(residuals: dict, out_dir: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle("Noise Residuals", fontsize=14, fontweight="bold")

    panels = [
        ("wiener",   "Wiener Filter Residual\n(PRNU-style)"),
        ("gaussian", "Gaussian Residual\n(σ=1.0)"),
        ("median",   "Median Filter Residual\n(3×3)"),
    ]

    for ax, (key, title) in zip(axes, panels):
        res = residuals[key].astype(np.float64)
        enhanced = res - res.min()
        if enhanced.max() > 0:
            enhanced /= enhanced.max()
        ax.imshow(enhanced, cmap="gray", vmin=0, vmax=1)
        ax.set_title(title, fontsize=10)
        ax.axis("off")
        ax.text(
            0.02, 0.02,
            f"σ={np.std(res):.4f}\npeak={np.max(np.abs(res)):.4f}",
            transform=ax.transAxes, fontsize=7, color="white",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="black", alpha=0.65),
        )

    plt.tight_layout()
    fig.savefig(out_dir / "residual.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# FFT spectrum + radial energy profile
# ---------------------------------------------------------------------------

def _save_spectrum(processed: dict, out_dir: Path) -> None:
    gray = processed["gray_norm"]
    h, w = gray.shape

    window = np.outer(np.hanning(h), np.hanning(w))
    spectrum = np.abs(fftshift(fft2(gray * window)))
    log_spectrum = np.log1p(spectrum)

    # Build radial energy profile
    cy, cx = h // 2, w // 2
    y_idx, x_idx = np.ogrid[:h, :w]
    norm_dist = np.sqrt((y_idx - cy) ** 2 + (x_idx - cx) ** 2) / (min(cy, cx) + 1e-10)

    n_bins = 50
    profile = np.zeros(n_bins)
    bin_edges = np.linspace(0, 0.5, n_bins + 1)
    for i in range(n_bins):
        mask = (norm_dist >= bin_edges[i]) & (norm_dist < bin_edges[i + 1])
        if mask.sum() > 0:
            profile[i] = log_spectrum[mask].mean()
    x_axis = (bin_edges[:-1] + bin_edges[1:]) / 2

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    ax1.imshow(log_spectrum, cmap="inferno", origin="upper")
    ax1.set_title("FFT Magnitude Spectrum (log scale)", fontsize=12)
    ax1.axis("off")

    low_idx = int(FFT_LOW_CUTOFF * n_bins * 2)
    mid_idx = int(FFT_MID_CUTOFF * n_bins * 2)

    ax2.plot(x_axis, profile, color="#1a73e8", linewidth=2, label="Radial energy")
    ax2.axvline(FFT_LOW_CUTOFF, color="#34a853", linestyle="--", alpha=0.8,
                label=f"Low/Mid ({FFT_LOW_CUTOFF})")
    ax2.axvline(FFT_MID_CUTOFF, color="#ea4335", linestyle="--", alpha=0.8,
                label=f"Mid/High ({FFT_MID_CUTOFF})")
    ax2.fill_between(x_axis[:low_idx], profile[:low_idx], alpha=0.15,
                     color="#34a853", label="Low band")
    ax2.fill_between(x_axis[low_idx:mid_idx], profile[low_idx:mid_idx],
                     alpha=0.15, color="#fbbc04", label="Mid band")
    ax2.fill_between(x_axis[mid_idx:], profile[mid_idx:], alpha=0.15,
                     color="#ea4335", label="High band")
    ax2.set_xlabel("Normalised Frequency (0=DC, 0.5=Nyquist)")
    ax2.set_ylabel("Mean Log Energy")
    ax2.set_title("Radial Energy Profile", fontsize=12)
    ax2.legend(fontsize=8, loc="upper right")
    ax2.grid(True, alpha=0.25)

    plt.tight_layout()
    fig.savefig(out_dir / "spectrum.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Local noise variance heatmap
# ---------------------------------------------------------------------------

def _save_heatmap(features: dict, out_dir: Path) -> None:
    variance_map = features["maps"]["variance_map"]

    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(variance_map, cmap="hot", interpolation="bilinear")
    ax.set_title(
        "Local Noise Variance Map\n(bright = high noise, dark = smooth region)",
        fontsize=12,
    )
    ax.axis("off")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)

    plt.tight_layout()
    fig.savefig(out_dir / "heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Per-channel noise panel
# ---------------------------------------------------------------------------

def _save_channel_noise(residuals: dict, out_dir: Path) -> None:
    ch_res = residuals["per_channel"]   # H×W×3

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    fig.suptitle(
        "Per-Channel Noise Residuals (Wiener)\n"
        "High cross-channel correlation → camera-like",
        fontsize=13, fontweight="bold",
    )

    channels = [
        (0, "Red Channel",   "Reds"),
        (1, "Green Channel", "Greens"),
        (2, "Blue Channel",  "Blues"),
    ]
    for ax, (c, name, cmap) in zip(axes, channels):
        res = ch_res[:, :, c].astype(np.float64)
        enhanced = res - res.min()
        if enhanced.max() > 0:
            enhanced /= enhanced.max()
        ax.imshow(enhanced, cmap=cmap, vmin=0, vmax=1)
        ax.set_title(f"{name}\nσ={np.std(res):.5f}", fontsize=10)
        ax.axis("off")

    plt.tight_layout()
    fig.savefig(out_dir / "channel_noise.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

import numpy as np
from scipy.ndimage import gaussian_filter, sobel
from scipy.fft import fft2, fftshift
from config import TILE_SIZE, FFT_LOW_CUTOFF, FFT_MID_CUTOFF
from core.utils import linear_map, safe_corrcoef


def extract_features(image_data: dict, processed: dict, residuals: dict) -> dict:
    is_small = processed["is_small"]
    is_grayscale = processed["is_grayscale"]

    exif_score, exif_details = _exif_score(image_data)
    spectral_score, spectral_details = _spectral_score(processed["gray_norm"])
    texture_score, texture_details = _texture_score(processed["gray_norm"])
    isotropy_score, isotropy_details = _isotropy_score(processed["gray_norm"])

    if is_grayscale:
        # Channel covariance is meaningless when all channels are copies of the same plane
        cov_score, cov_details = 0.5, {"note": "original image is grayscale — feature skipped"}
    elif is_small:
        cov_score, cov_details = 0.5, {"note": "image too small"}
    else:
        cov_score, cov_details = _channel_covariance_score(residuals["per_channel"])

    if is_small:
        variance_score, variance_details = 0.5, {"note": "image too small for tile analysis"}
    else:
        variance_score, variance_details = _local_variance_score(
            residuals["wiener"], processed["gray_norm"]
        )

    return {
        "scores": {
            "exif": exif_score,
            "spectral": spectral_score,
            "channel_covariance": cov_score,
            "local_variance": variance_score,
            "texture": texture_score,
            "isotropy": isotropy_score,
        },
        "details": {
            "exif": exif_details,
            "spectral": spectral_details,
            "channel_covariance": cov_details,
            "local_variance": variance_details,
            "texture": texture_details,
            "isotropy": isotropy_details,
        },
        "maps": {
            "variance_map": _compute_variance_map(residuals["wiener"]),
        },
        "is_small": is_small,
        "jpeg_quality": image_data["jpeg_quality"],
    }


# ---------------------------------------------------------------------------
# Individual feature functions
# Each returns (score: float in [0,1], details: dict)
# Score convention: 0 = strongly synthetic, 1 = strongly camera
# ---------------------------------------------------------------------------

def _exif_score(image_data: dict) -> tuple[float, dict]:
    exif = image_data["exif"]
    camera_fields = image_data["exif_camera_fields"]

    if not exif:
        return 0.0, {"has_exif": False, "camera_fields": 0,
                     "note": "no EXIF data — common for AI-generated images"}

    score = 0.15  # has any EXIF at all

    if "Make" in camera_fields or "Model" in camera_fields:
        score += 0.45  # camera make/model is the strongest single signal

    exposure_fields = {"ExposureTime", "FNumber", "ISOSpeedRatings", "ExposureBiasValue"}
    found_exposure = len(exposure_fields & camera_fields)
    score += min(found_exposure * 0.10, 0.25)

    if "GPSInfo" in camera_fields:
        score += 0.10  # GPS is almost exclusively camera-originated

    if "FocalLength" in camera_fields:
        score += 0.05

    return float(np.clip(score, 0.0, 1.0)), {
        "has_exif": True,
        "camera_fields_count": len(camera_fields),
        "camera_fields": sorted(camera_fields),
        "make": str(exif.get("Make", "")),
        "model": str(exif.get("Model", "")),
    }


def _spectral_score(gray: np.ndarray) -> tuple[float, dict]:
    """
    Radial energy distribution in log-FFT spectrum.

    Camera images follow a 1/f² power law with a characteristic high-frequency
    noise floor from sensor shot noise. Diffusion models tend to suppress
    high-frequency energy, producing a steeper spectral rolloff.

    Key finding from FreqCross (2025): the 0.1–0.4 normalised frequency band
    has distinctive signatures. We use the high-frequency energy ratio as the
    primary discriminator.
    """
    h, w = gray.shape

    # Hann window reduces spectral leakage from image boundaries
    window = np.outer(np.hanning(h), np.hanning(w))
    spectrum = np.abs(fftshift(fft2(gray * window)))
    log_spectrum = np.log1p(spectrum)

    cy, cx = h // 2, w // 2
    y_idx, x_idx = np.ogrid[:h, :w]
    radial_dist = np.sqrt((y_idx - cy) ** 2 + (x_idx - cx) ** 2)
    max_dist = float(min(cy, cx))

    if max_dist < 1:
        return 0.5, {"note": "image too small for spectral analysis"}

    norm_dist = radial_dist / max_dist

    low_mask = norm_dist <= FFT_LOW_CUTOFF
    mid_mask = (norm_dist > FFT_LOW_CUTOFF) & (norm_dist <= FFT_MID_CUTOFF)
    high_mask = (norm_dist > FFT_MID_CUTOFF) & (norm_dist <= 0.5)

    total = log_spectrum.sum() + 1e-10
    low_ratio = float(log_spectrum[low_mask].sum() / total)
    mid_ratio = float(log_spectrum[mid_mask].sum() / total)
    high_ratio = float(log_spectrum[high_mask].sum() / total)

    # Camera: high_ratio ≈ 0.15–0.30 | AI: high_ratio ≈ 0.05–0.15
    score = linear_map(high_ratio, 0.05, 0.28)

    # Penalty when mid-frequency band dominates relative to high (AI signature)
    mid_to_high = mid_ratio / (high_ratio + 1e-10)
    mid_penalty = linear_map(mid_to_high, 1.5, 3.5) * 0.20
    score = float(np.clip(score - mid_penalty, 0.0, 1.0))

    return score, {
        "low_ratio": low_ratio,
        "mid_ratio": mid_ratio,
        "high_ratio": high_ratio,
        "mid_to_high_ratio": float(mid_to_high),
    }


def _channel_covariance_score(channel_residuals: np.ndarray) -> tuple[float, dict]:
    """
    Cross-channel noise correlation as a Bayer demosaicing proxy.

    Camera sensors use a Bayer colour filter array. Demosaicing interpolates
    missing colour values from neighbours, introducing strong cross-channel
    correlations in the noise. AI generators produce colour images without
    this constraint, yielding much weaker channel correlations.
    """
    r = channel_residuals[:, :, 0].ravel()
    g = channel_residuals[:, :, 1].ravel()
    b = channel_residuals[:, :, 2].ravel()

    rg = safe_corrcoef(r, g)
    rb = safe_corrcoef(r, b)
    gb = safe_corrcoef(g, b)
    mean_corr = (abs(rg) + abs(rb) + abs(gb)) / 3.0

    # Camera: mean_corr ≈ 0.40–0.75  |  AI: mean_corr ≈ 0.05–0.30
    score = linear_map(mean_corr, 0.05, 0.70)

    return float(score), {
        "rg_correlation": rg,
        "rb_correlation": rb,
        "gb_correlation": gb,
        "mean_correlation": float(mean_corr),
    }


def _local_variance_score(residual: np.ndarray, gray: np.ndarray) -> tuple[float, dict]:
    """
    Two signals:
    1. Coefficient of variation of per-tile noise variance — camera noise is
       spatially structured; AI noise is more uniform.
    2. Correlation between local noise variance and local brightness — camera
       shot noise scales with signal level (Poisson process); AI does not.
    """
    h, w = residual.shape
    tile_h = max(TILE_SIZE, h // 16)
    tile_w = max(TILE_SIZE, w // 16)
    n_h = h // tile_h
    n_w = w // tile_w

    if n_h < 2 or n_w < 2:
        return 0.5, {"note": "too few tiles — image may be too small"}

    variances = []
    brightnesses = []
    for i in range(n_h):
        for j in range(n_w):
            r = residual[i * tile_h:(i + 1) * tile_h, j * tile_w:(j + 1) * tile_w]
            g = gray[i * tile_h:(i + 1) * tile_h, j * tile_w:(j + 1) * tile_w]
            variances.append(float(np.var(r)))
            brightnesses.append(float(np.mean(g)))

    variances = np.array(variances)
    brightnesses = np.array(brightnesses)

    mean_var = float(np.mean(variances)) + 1e-10
    cv = float(np.std(variances) / mean_var)

    # Shot-noise signature: variance ∝ brightness
    brightness_noise_corr = safe_corrcoef(variances, brightnesses)

    # Camera: cv ≈ 0.4–1.0  |  AI: cv ≈ 0.1–0.4
    cv_score = linear_map(cv, 0.10, 0.80)

    # Camera: corr ≈ 0.2–0.7  |  AI: corr ≈ −0.2–0.2
    corr_score = linear_map(brightness_noise_corr, -0.20, 0.65)

    score = 0.60 * cv_score + 0.40 * corr_score

    return float(np.clip(score, 0.0, 1.0)), {
        "coefficient_of_variation": cv,
        "brightness_noise_correlation": float(brightness_noise_corr),
        "n_tiles": int(n_h * n_w),
        "mean_variance": float(mean_var),
    }


def _texture_score(gray: np.ndarray) -> tuple[float, dict]:
    """
    Gradient magnitude as a proxy for optical sharpness.

    Real lenses produce sharp, high-contrast edges. Diffusion models generate
    images with characteristically smooth textures and weaker edges
    (Edge-Enhanced ViT paper, 2025).
    """
    gx = sobel(gray, axis=1)
    gy = sobel(gray, axis=0)
    grad_mag = np.sqrt(gx ** 2 + gy ** 2)

    mean_grad = float(np.mean(grad_mag))
    mean_intensity = float(np.mean(gray)) + 1e-10
    # Normalise by brightness so dark images are not unfairly penalised
    norm_grad = mean_grad / mean_intensity

    # Camera: norm_grad ≈ 0.30–1.00  |  AI: norm_grad ≈ 0.10–0.40
    score = linear_map(norm_grad, 0.10, 0.80)

    return float(score), {
        "mean_gradient_magnitude": mean_grad,
        "normalised_gradient": float(norm_grad),
        "mean_intensity": float(mean_intensity),
    }


def _isotropy_score(gray: np.ndarray) -> tuple[float, dict]:
    """
    Frequency-domain anisotropy in the mid-frequency ring.

    Natural camera images have strongly anisotropic spectra (horizontal/
    vertical edges from architecture, perspective lines, etc.). AI images
    tend toward more isotropic mid-frequency distributions.
    """
    h, w = gray.shape
    window = np.outer(np.hanning(h), np.hanning(w))
    spectrum = np.abs(fftshift(fft2(gray * window)))

    cy, cx = h // 2, w // 2
    y_idx, x_idx = np.ogrid[:h, :w]
    norm_dist = np.sqrt((y_idx - cy) ** 2 + (x_idx - cx) ** 2) / (min(cy, cx) + 1e-10)

    mid_ring = (norm_dist > FFT_LOW_CUTOFF) & (norm_dist <= FFT_MID_CUTOFF)
    angles = np.arctan2((y_idx - cy), (x_idx - cx))  # (−π, π]

    n_sectors = 8
    sector_energies = []
    for i in range(n_sectors):
        lo = -np.pi + i * (2 * np.pi / n_sectors)
        hi = -np.pi + (i + 1) * (2 * np.pi / n_sectors)
        mask = mid_ring & (angles >= lo) & (angles < hi)
        if mask.sum() > 0:
            sector_energies.append(float(spectrum[mask].mean()))

    if len(sector_energies) < 4:
        return 0.5, {"note": "insufficient sector coverage"}

    arr = np.array(sector_energies)
    cv_sectors = float(np.std(arr) / (np.mean(arr) + 1e-10))

    # Camera (anisotropic): cv ≈ 0.20–0.50  |  AI (isotropic): cv ≈ 0.05–0.20
    score = linear_map(cv_sectors, 0.05, 0.45)

    return float(score), {
        "angular_cv": cv_sectors,
        "n_sectors": len(sector_energies),
        "sector_energies": [round(e, 6) for e in sector_energies],
    }


def _compute_variance_map(residual: np.ndarray) -> np.ndarray:
    """Smooth local variance map for heatmap visualisation."""
    sq = residual ** 2
    mean_sq = gaussian_filter(sq.astype(np.float64), sigma=8)
    mean = gaussian_filter(residual.astype(np.float64), sigma=8)
    variance_map = mean_sq - mean ** 2
    return np.clip(variance_map, 0, None).astype(np.float32)

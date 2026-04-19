import numpy as np
from scipy.signal import wiener
from scipy.ndimage import gaussian_filter, median_filter


def extract_residuals(processed: dict) -> dict:
    gray = processed["gray_norm"]   # H×W, float32 [0,1]
    rgb = processed["rgb_norm"]     # H×W×3, float32 [0,1]

    wiener_res = _wiener_residual(gray)
    gaussian_res = _gaussian_residual(gray)
    median_res = _median_residual(gray)

    # Per-channel Wiener residuals for cross-channel covariance analysis
    per_channel = np.stack(
        [_wiener_residual(rgb[:, :, c]) for c in range(3)], axis=-1
    )

    return {
        "wiener": wiener_res,
        "gaussian": gaussian_res,
        "median": median_res,
        "per_channel": per_channel,   # H×W×3
    }


def _wiener_residual(img: np.ndarray) -> np.ndarray:
    import warnings
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            filtered = wiener(img.astype(np.float64), mysize=5)
        # Wiener can return NaN in zero-variance regions; fall back to 0
        filtered = np.nan_to_num(filtered, nan=0.0)
        return (img.astype(np.float64) - filtered).astype(np.float32)
    except Exception:
        return _gaussian_residual(img)


def _gaussian_residual(img: np.ndarray) -> np.ndarray:
    filtered = gaussian_filter(img.astype(np.float64), sigma=1.0)
    return (img.astype(np.float64) - filtered).astype(np.float32)


def _median_residual(img: np.ndarray) -> np.ndarray:
    filtered = median_filter(img.astype(np.float64), size=3)
    return (img.astype(np.float64) - filtered).astype(np.float32)

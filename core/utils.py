import numpy as np


def linear_map(value: float, low: float, high: float) -> float:
    """Map value linearly from [low, high] → [0, 1], clamped."""
    return float(np.clip((value - low) / (high - low + 1e-10), 0.0, 1.0))


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return float(np.clip(value, lo, hi))


def safe_corrcoef(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson correlation, returning 0.0 on degenerate input."""
    if np.std(a) < 1e-10 or np.std(b) < 1e-10:
        return 0.0
    result = np.corrcoef(a, b)[0, 1]
    return 0.0 if np.isnan(result) else float(result)

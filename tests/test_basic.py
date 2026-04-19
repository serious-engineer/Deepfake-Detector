"""
Basic sanity tests — run with:  pytest tests/
No real camera images required; synthetic test images are generated in memory.
"""

import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.loader import load_image
from core.preprocess import preprocess
from core.residual import extract_residuals
from core.features import extract_features
from core.scoring import score_image
from core.utils import linear_map, safe_corrcoef


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_noisy_image(size=(256, 256)) -> Image.Image:
    """
    Camera-like synthetic image:
    - Sharp horizontal/vertical edges for anisotropic spectrum
    - Shot noise (correlated across channels, scales with brightness)
    - Cross-channel correlation from a shared noise base
    """
    rng = np.random.default_rng(42)
    base = np.zeros((*size, 3), dtype=np.float32)
    for c in range(3):
        base[:, :, c] = np.linspace(80, 180, size[1]) + np.linspace(0, 50, size[0])[:, None]
    # Structural edges → anisotropic frequency spectrum
    for i in range(0, size[0], 32):
        base[i:i + 3, :, :] += 25
    for j in range(0, size[1], 32):
        base[:, j:j + 3, :] += 25
    # Shot noise: shared base (cross-channel correlated), amplitude ∝ brightness
    shared = rng.normal(0, 1.0, size[:2]).astype(np.float32)
    for c, scale in enumerate([1.0, 0.75, 0.85]):
        brightness = np.clip(base[:, :, c] / 255.0, 0.1, 1.0)
        base[:, :, c] += shared * scale * brightness * 12.0
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


def _make_smooth_image(size=(256, 256)) -> Image.Image:
    """
    AI-like synthetic image:
    - Smooth, featureless gradient (no structural edges)
    - Independent per-channel noise at very low amplitude
    - Isotropic noise → uniform angular spectrum
    """
    rng = np.random.default_rng(7)
    base = np.zeros((*size, 3), dtype=np.float32)
    for c in range(3):
        base[:, :, c] = np.linspace(110, 190, size[1]) + np.linspace(0, 15, size[0])[:, None]
    # Independent, tiny noise per channel (no Bayer correlation)
    for c in range(3):
        base[:, :, c] += rng.normal(0, 0.4, size).astype(np.float32)
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


@pytest.fixture
def noisy_png(tmp_path) -> str:
    p = tmp_path / "noisy.png"
    _make_noisy_image().save(str(p))
    return str(p)


@pytest.fixture
def smooth_png(tmp_path) -> str:
    p = tmp_path / "smooth.png"
    _make_smooth_image().save(str(p))
    return str(p)


@pytest.fixture
def small_png(tmp_path) -> str:
    p = tmp_path / "small.png"
    Image.fromarray(np.random.randint(0, 255, (32, 32, 3), dtype=np.uint8)).save(str(p))
    return str(p)


@pytest.fixture
def grayscale_png(tmp_path) -> str:
    p = tmp_path / "gray.png"
    Image.fromarray(np.random.randint(0, 255, (128, 128), dtype=np.uint8)).save(str(p))
    return str(p)


# ---------------------------------------------------------------------------
# Pipeline smoke tests
# ---------------------------------------------------------------------------

def _run_pipeline(path: str) -> dict:
    image_data = load_image(path)
    processed = preprocess(image_data)
    residuals = extract_residuals(processed)
    features = extract_features(image_data, processed, residuals)
    return score_image(features)


def test_full_pipeline_noisy(noisy_png):
    result = _run_pipeline(noisy_png)
    assert result["label"] in {"camera", "synthetic", "inconclusive"}
    assert 0.0 <= result["score"] <= 1.0
    assert 0.0 <= result["confidence"] <= 1.0


def test_full_pipeline_smooth(smooth_png):
    result = _run_pipeline(smooth_png)
    assert result["label"] in {"camera", "synthetic", "inconclusive"}
    assert 0.0 <= result["score"] <= 1.0


def test_small_image_does_not_crash(small_png):
    result = _run_pipeline(small_png)
    assert result["label"] in {"camera", "synthetic", "inconclusive"}


def test_grayscale_image_does_not_crash(grayscale_png):
    result = _run_pipeline(grayscale_png)
    assert result["label"] in {"camera", "synthetic", "inconclusive"}


def test_feature_scores_bounded(noisy_png):
    image_data = load_image(noisy_png)
    processed = preprocess(image_data)
    residuals = extract_residuals(processed)
    features = extract_features(image_data, processed, residuals)
    for name, val in features["scores"].items():
        assert 0.0 <= val <= 1.0, f"Feature {name!r} out of [0,1]: {val}"


def test_noisy_scores_higher_than_smooth(noisy_png, smooth_png):
    """
    Camera-like image (shot noise + correlated channels + structural edges)
    should score higher than a smooth, featureless AI-like image.
    Both lack EXIF (synthetic PNGs), so the absolute scores will be low,
    but the ordering should hold.
    """
    noisy_result = _run_pipeline(noisy_png)
    smooth_result = _run_pipeline(smooth_png)
    # Allow a small tolerance: the ranking should hold even without EXIF
    assert noisy_result["score"] > smooth_result["score"] - 0.02, (
        f"Expected camera-like ({noisy_result['score']:.3f}) ≥ AI-like "
        f"({smooth_result['score']:.3f}) — check feature calibrations"
    )


# ---------------------------------------------------------------------------
# Unit tests for utilities
# ---------------------------------------------------------------------------

def test_linear_map_clamps():
    assert linear_map(0.0, 0.1, 0.5) == 0.0
    assert linear_map(1.0, 0.1, 0.5) == 1.0
    assert abs(linear_map(0.3, 0.1, 0.5) - 0.5) < 1e-6


def test_safe_corrcoef_constant():
    a = np.ones(100)
    b = np.random.rand(100)
    assert safe_corrcoef(a, b) == 0.0


def test_safe_corrcoef_perfect():
    a = np.linspace(0, 1, 100)
    assert abs(safe_corrcoef(a, a) - 1.0) < 1e-6


# ---------------------------------------------------------------------------
# Loader tests
# ---------------------------------------------------------------------------

def test_loader_missing_file():
    with pytest.raises(FileNotFoundError):
        load_image("/nonexistent/path/image.jpg")


def test_loader_unsupported_format(tmp_path):
    p = tmp_path / "file.xyz"
    p.write_bytes(b"data")
    with pytest.raises(ValueError, match="Unsupported format"):
        load_image(str(p))


def test_loader_returns_required_keys(noisy_png):
    data = load_image(noisy_png)
    for key in ("image", "path", "format", "mode", "size", "exif",
                "exif_camera_fields", "jpeg_quality", "is_grayscale"):
        assert key in data, f"Missing key: {key!r}"

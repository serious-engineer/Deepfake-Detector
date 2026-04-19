import numpy as np
from config import FEATURE_WEIGHTS, SYNTHETIC_THRESHOLD, CAMERA_THRESHOLD


def score_image(features: dict) -> dict:
    scores = features["scores"]

    weighted_sum = 0.0
    total_weight = 0.0
    for feature, weight in FEATURE_WEIGHTS.items():
        s = scores.get(feature, 0.5)
        if np.isfinite(s):
            weighted_sum += s * weight
            total_weight += weight

    raw_score = weighted_sum / total_weight if total_weight > 0 else 0.5

    # Heavy JPEG compression degrades forensic signals — shrink confidence toward 0.5
    jpeg_quality = features.get("jpeg_quality")
    if jpeg_quality is not None and jpeg_quality < 70:
        attenuation = 0.5 + (0.5 - abs(jpeg_quality - 70) / 70) * 0.3
        raw_score = 0.5 + (raw_score - 0.5) * attenuation

    # Small images give unreliable features
    if features.get("is_small"):
        raw_score = 0.5 + (raw_score - 0.5) * 0.50

    final_score = float(np.clip(raw_score, 0.0, 1.0))

    if final_score < SYNTHETIC_THRESHOLD:
        label = "synthetic"
    elif final_score > CAMERA_THRESHOLD:
        label = "camera"
    else:
        label = "inconclusive"

    confidence = _compute_confidence(final_score, label)

    return {
        "score": final_score,
        "label": label,
        "confidence": float(confidence),
        "feature_scores": {k: float(v) for k, v in scores.items()},
    }


def _compute_confidence(score: float, label: str) -> float:
    """Confidence = normalised distance from the nearest decision boundary."""
    if label == "synthetic":
        return float(np.clip((SYNTHETIC_THRESHOLD - score) / SYNTHETIC_THRESHOLD, 0.0, 1.0))
    if label == "camera":
        return float(np.clip((score - CAMERA_THRESHOLD) / (1.0 - CAMERA_THRESHOLD), 0.0, 1.0))
    # inconclusive: proximity to the centre of the grey zone
    zone_half = (CAMERA_THRESHOLD - SYNTHETIC_THRESHOLD) / 2.0
    distance_from_centre = abs(score - 0.5)
    return float(np.clip(1.0 - distance_from_centre / zone_half, 0.0, 1.0))

import numpy as np
from PIL import Image
from config import MAX_DIMENSION


def preprocess(image_data: dict) -> dict:
    img = image_data["image"]
    original_size = img.size  # (w, h)

    img = _resize_if_needed(img, MAX_DIMENSION)
    processed_size = img.size

    rgb_img = img.convert("RGB")
    gray_img = rgb_img.convert("L")

    rgb_array = np.array(rgb_img, dtype=np.float32)      # H×W×3, [0,255]
    gray_array = np.array(gray_img, dtype=np.float32)    # H×W,   [0,255]

    rgb_norm = rgb_array / 255.0
    gray_norm = gray_array / 255.0

    h, w = gray_array.shape
    is_small = min(h, w) < 64

    return {
        "rgb": rgb_array,
        "rgb_norm": rgb_norm,
        "gray": gray_array,
        "gray_norm": gray_norm,
        "original_size": original_size,
        "processed_size": processed_size,
        "is_small": is_small,
        "is_grayscale": image_data["is_grayscale"],
    }


def _resize_if_needed(img: Image.Image, max_dim: int) -> Image.Image:
    w, h = img.size
    if max(w, h) <= max_dim:
        return img
    scale = max_dim / max(w, h)
    return img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

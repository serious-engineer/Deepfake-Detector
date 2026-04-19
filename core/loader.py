from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
from config import SUPPORTED_FORMATS

# EXIF tags that are only present on images captured by a real camera
CAMERA_EXIF_FIELDS = {
    "Make", "Model", "ExposureTime", "FNumber", "ISOSpeedRatings",
    "FocalLength", "Flash", "WhiteBalance", "MeteringMode",
    "ExposureMode", "SceneCaptureType", "GPSInfo", "LightSource",
    "ExposureBiasValue", "MaxApertureValue", "FocalLengthIn35mmFilm",
    "DigitalZoomRatio", "Sharpness", "Saturation",
}


def load_image(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Image not found: {path}")

    suffix = p.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format: {suffix!r}. Supported: {sorted(SUPPORTED_FORMATS)}"
        )

    img = Image.open(p)
    img.load()  # force full decode before file handle closes

    exif_data, camera_fields_found = _extract_exif(img)
    is_grayscale = img.mode in {"L", "1", "LA", "P"}
    jpeg_quality = _estimate_jpeg_quality(img) if suffix in {".jpg", ".jpeg"} else None

    return {
        "image": img,
        "path": p,
        "format": suffix.lstrip(".").upper(),
        "mode": img.mode,
        "size": img.size,  # (width, height)
        "is_grayscale": is_grayscale,
        "exif": exif_data,
        "exif_camera_fields": camera_fields_found,
        "jpeg_quality": jpeg_quality,
    }


def _extract_exif(img: Image.Image) -> tuple[dict, set]:
    exif_data: dict = {}
    camera_fields_found: set = set()
    try:
        exif_obj = img.getexif()
        for tag_id, value in exif_obj.items():
            tag = TAGS.get(tag_id, str(tag_id))
            # Stringify bytes to avoid serialisation issues later
            if isinstance(value, bytes):
                try:
                    value = value.decode("utf-8", errors="replace")
                except Exception:
                    value = repr(value)
            exif_data[tag] = value
            if tag in CAMERA_EXIF_FIELDS:
                camera_fields_found.add(tag)
    except Exception:
        pass
    return exif_data, camera_fields_found


def _estimate_jpeg_quality(img: Image.Image) -> int | None:
    """Rough JPEG quality estimate from quantization table sum."""
    try:
        qtables = img.quantization
        if qtables and 0 in qtables:
            q_sum = sum(qtables[0])
            if q_sum < 700:
                return 95
            elif q_sum < 1000:
                return 85
            elif q_sum < 1300:
                return 75
            elif q_sum < 1700:
                return 65
            else:
                return 50
    except Exception:
        pass
    return None

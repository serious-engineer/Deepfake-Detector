from pathlib import Path

SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}

# Images larger than this are downscaled before analysis (preserves forensic signals)
MAX_DIMENSION = 2048

# Tile size for local variance analysis
TILE_SIZE = 32

# Normalized frequency band boundaries (0 = DC, 0.5 = Nyquist)
FFT_LOW_CUTOFF = 0.10
FFT_MID_CUTOFF = 0.40

# Classification thresholds on the [0=synthetic, 1=camera] scale
SYNTHETIC_THRESHOLD = 0.38
CAMERA_THRESHOLD = 0.62

# Feature weights — must sum to 1.0
FEATURE_WEIGHTS: dict[str, float] = {
    "exif": 0.20,
    "spectral": 0.20,
    "channel_covariance": 0.20,
    "local_variance": 0.15,
    "texture": 0.15,
    "isotropy": 0.10,
}

OUTPUT_DIR = Path("forensics_output")

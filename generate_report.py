"""
Project Report Generator
Produces a self-contained PDF technical report for the
Image Noise Forensics Tool (Deepfake-Detector project).

Run:  python generate_report.py
Output: Project_Report_Image_Noise_Forensics.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, Preformatted, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import Flowable
import os

# ---------------------------------------------------------------------------
# Output path
# ---------------------------------------------------------------------------
OUTPUT_FILE = os.path.join(os.path.dirname(__file__),
                           "Project_Report_Image_Noise_Forensics.pdf")

PAGE_W, PAGE_H = A4
MARGIN = 2.2 * cm

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
C_DARK   = colors.HexColor("#1a1a2e")
C_BLUE   = colors.HexColor("#1a73e8")
C_GREEN  = colors.HexColor("#1e6f45")
C_RED    = colors.HexColor("#842029")
C_AMBER  = colors.HexColor("#b45309")
C_LIGHT  = colors.HexColor("#f0f4ff")
C_GREY   = colors.HexColor("#666666")
C_SILVER = colors.HexColor("#e8eaed")
C_CODE   = colors.HexColor("#1e1e2e")
C_CODEBG = colors.HexColor("#f5f5f5")

# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
base_styles = getSampleStyleSheet()

def S(name, **kw):
    return ParagraphStyle(name, **kw)

styles = {
    "cover_title": S("cover_title",
        fontName="Helvetica-Bold", fontSize=28, leading=36,
        textColor=C_DARK, alignment=TA_CENTER, spaceAfter=8),

    "cover_sub": S("cover_sub",
        fontName="Helvetica", fontSize=13, leading=18,
        textColor=C_GREY, alignment=TA_CENTER, spaceAfter=4),

    "h1": S("h1",
        fontName="Helvetica-Bold", fontSize=17, leading=22,
        textColor=C_DARK, spaceBefore=22, spaceAfter=10,
        borderPad=4),

    "h2": S("h2",
        fontName="Helvetica-Bold", fontSize=13, leading=17,
        textColor=C_BLUE, spaceBefore=16, spaceAfter=6),

    "h3": S("h3",
        fontName="Helvetica-BoldOblique", fontSize=11, leading=15,
        textColor=C_DARK, spaceBefore=12, spaceAfter=4),

    "body": S("body",
        fontName="Helvetica", fontSize=10, leading=15,
        textColor=C_DARK, alignment=TA_JUSTIFY,
        spaceAfter=6),

    "body_left": S("body_left",
        fontName="Helvetica", fontSize=10, leading=15,
        textColor=C_DARK, spaceAfter=4),

    "caption": S("caption",
        fontName="Helvetica-Oblique", fontSize=9, leading=12,
        textColor=C_GREY, alignment=TA_CENTER, spaceAfter=8),

    "bullet": S("bullet",
        fontName="Helvetica", fontSize=10, leading=14,
        textColor=C_DARK, leftIndent=18, spaceAfter=3,
        bulletIndent=6),

    "code_label": S("code_label",
        fontName="Helvetica-Bold", fontSize=8.5, leading=11,
        textColor=C_BLUE, spaceBefore=10, spaceAfter=2),

    "note": S("note",
        fontName="Helvetica-Oblique", fontSize=9, leading=13,
        textColor=C_AMBER, spaceAfter=6),

    "toc_h1": S("toc_h1",
        fontName="Helvetica-Bold", fontSize=10.5, leading=14,
        textColor=C_DARK, spaceAfter=4),

    "toc_h2": S("toc_h2",
        fontName="Helvetica", fontSize=10, leading=13,
        textColor=C_GREY, leftIndent=18, spaceAfter=2),
}

# ---------------------------------------------------------------------------
# Helper flowables
# ---------------------------------------------------------------------------

def H1(text):
    return [
        HRFlowable(width="100%", thickness=2, color=C_DARK, spaceAfter=6),
        Paragraph(text, styles["h1"]),
    ]

def H2(text):
    return [Paragraph(text, styles["h2"])]

def H3(text):
    return [Paragraph(text, styles["h3"])]

def P(text):
    return Paragraph(text, styles["body"])

def PL(text):
    return Paragraph(text, styles["body_left"])

def Bul(items):
    return [Paragraph(f"• {i}", styles["bullet"]) for i in items]

def SP(n=6):
    return Spacer(1, n)

def code_block(label, code_text):
    elems = []
    if label:
        elems.append(Paragraph(label, styles["code_label"]))
    lines = code_text.strip("\n")
    pre = Preformatted(lines, ParagraphStyle(
        "code",
        fontName="Courier", fontSize=7.8, leading=11.5,
        textColor=C_CODE, backColor=C_CODEBG,
        leftIndent=10, rightIndent=10,
        borderPad=8, spaceAfter=8,
    ))
    elems.append(pre)
    return elems

def info_table(rows, col_widths=None):
    """Two-column label/value table."""
    data = [[Paragraph(f"<b>{k}</b>", styles["body_left"]),
             Paragraph(v, styles["body_left"])] for k, v in rows]
    cw = col_widths or [6*cm, PAGE_W - 2*MARGIN - 6*cm]
    t = Table(data, colWidths=cw)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), colors.white),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [colors.white, C_SILVER]),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
        ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    return t

def feature_table(rows):
    """Feature summary table with headers."""
    header = [
        Paragraph("<b>Feature</b>", styles["body_left"]),
        Paragraph("<b>Signal Measured</b>", styles["body_left"]),
        Paragraph("<b>Weight</b>", styles["body_left"]),
        Paragraph("<b>Camera Typical</b>", styles["body_left"]),
        Paragraph("<b>AI Typical</b>", styles["body_left"]),
    ]
    data = [header] + [
        [Paragraph(r[0], styles["body_left"]),
         Paragraph(r[1], styles["body_left"]),
         Paragraph(r[2], styles["body_left"]),
         Paragraph(r[3], styles["body_left"]),
         Paragraph(r[4], styles["body_left"])]
        for r in rows
    ]
    cw = [3.8*cm, 5.5*cm, 1.8*cm, 3.0*cm, 3.0*cm]
    t = Table(data, colWidths=cw)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), C_DARK),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, C_SILVER]),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    return t

# ---------------------------------------------------------------------------
# Document assembly
# ---------------------------------------------------------------------------

def build_story():
    story = []

    # -----------------------------------------------------------------------
    # Cover page
    # -----------------------------------------------------------------------
    story += [SP(80)]
    story.append(Paragraph("Image Noise Forensics Tool", styles["cover_title"]))
    story.append(Paragraph("Technical Project Report", styles["cover_sub"]))
    story += [SP(6)]
    story.append(HRFlowable(width="60%", thickness=2, color=C_BLUE,
                             hAlign="CENTER", spaceAfter=12))
    story.append(Paragraph(
        "Camera vs. AI-Generated Image Detection via Noise Residual Analysis",
        styles["cover_sub"]))
    story += [SP(40)]
    story.append(Paragraph("Version 1.0  ·  Phase 1 Complete", styles["cover_sub"]))
    story.append(Paragraph("Language: Python 3.10+", styles["cover_sub"]))
    story.append(Paragraph(
        "Repository: github.com/serious-engineer/Deepfake-Detector",
        styles["cover_sub"]))
    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # Table of Contents
    # -----------------------------------------------------------------------
    story += H1("Table of Contents")
    toc = [
        ("1.", "Abstract"),
        ("2.", "Methodology"),
        ("3.", "Theory & Signal Processing Background"),
        ("  3.1", "Noise Residuals"),
        ("  3.2", "EXIF Metadata"),
        ("  3.3", "Frequency-Domain Analysis (FFT)"),
        ("  3.4", "Cross-Channel Noise Correlation"),
        ("  3.5", "Local Variance Structure"),
        ("  3.6", "Texture / Edge Sharpness"),
        ("  3.7", "Frequency Anisotropy"),
        ("4.", "Architecture & Block Diagrams"),
        ("  4.1", "Full Processing Pipeline"),
        ("  4.2", "Feature Extraction Detail"),
        ("  4.3", "Scoring Logic"),
        ("5.", "Code Walkthrough"),
        ("  5.1", "config.py — Constants & Weights"),
        ("  5.2", "core/utils.py — Utility Functions"),
        ("  5.3", "core/loader.py — Image Loading"),
        ("  5.4", "core/preprocess.py — Preprocessing"),
        ("  5.5", "core/residual.py — Residual Extraction"),
        ("  5.6", "core/features.py — Feature Extractors"),
        ("  5.7", "core/scoring.py — Scoring & Verdict"),
        ("  5.8", "output/visualization.py — Visualisations"),
        ("  5.9", "output/report.py — HTML Report"),
        ("  5.10", "main.py — CLI Entry Point"),
        ("  5.11", "tests/test_basic.py — Test Suite"),
        ("6.", "Limitations"),
        ("7.", "Roadmap"),
        ("8.", "References"),
    ]
    for num, title in toc:
        indent = 30 if num.startswith("  ") else 0
        st = styles["toc_h2"] if num.startswith("  ") else styles["toc_h1"]
        story.append(Paragraph(f"{num.strip()}. {title}" if not num.startswith("  ")
                               else f"  {num.strip()}  {title}", st))
    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # 1. Abstract
    # -----------------------------------------------------------------------
    story += H1("1. Abstract")
    story.append(P(
        "This report documents the design, theory, and implementation of the "
        "<b>Image Noise Forensics Tool</b> — a Python command-line application "
        "that analyses the noise patterns embedded in a digital image to estimate "
        "whether it was captured by a real camera or synthesised by a diffusion "
        "model or GAN."
    ))
    story.append(P(
        "The tool extracts six independent forensic signals from the image's noise "
        "residual layer, metadata, and frequency spectrum. A weighted average of "
        "these signals produces a composite score in [0, 1], where 0 indicates "
        "synthetic origin and 1 indicates camera origin. The current phase (Phase 1) "
        "uses fully heuristic, signal-processing-based features without any trained "
        "machine-learning model."
    ))
    story.append(Paragraph(
        "<i>Disclaimer: This tool produces heuristic estimates. It is not a reliable "
        "forensic instrument for legal, journalistic, or evidentiary use.</i>",
        styles["note"]))
    story += [SP(8)]

    # -----------------------------------------------------------------------
    # 2. Methodology
    # -----------------------------------------------------------------------
    story += H1("2. Methodology")
    story.append(P(
        "The fundamental insight behind noise-based forensics is that every real "
        "camera sensor imprints a characteristic noise signature on captured images. "
        "This signature arises from three physical sources:"
    ))
    story += Bul([
        "<b>Photon shot noise</b> — quantum fluctuations in photon arrival; "
        "follows a Poisson distribution and scales with signal level (brightness).",
        "<b>Bayer demosaicing</b> — most sensors capture only one colour channel "
        "per pixel using a colour filter array. The missing channels are interpolated "
        "from neighbours, introducing strong spatial cross-channel correlations in "
        "the noise.",
        "<b>Photo Response Non-Uniformity (PRNU)</b> — fixed-pattern noise from "
        "pixel-to-pixel sensitivity variations; unique to each sensor.",
    ])
    story.append(P(
        "AI-generated images (from diffusion models or GANs) are synthesised "
        "mathematically. They do not pass through a physical sensor, so they lack "
        "these physical noise signatures. Diffusion models additionally suppress "
        "high-frequency content (smooth textures) and produce isotropic frequency "
        "distributions that differ from natural camera images."
    ))
    story.append(P(
        "The methodology follows a five-stage pipeline:"
    ))
    story += Bul([
        "<b>Load</b> — decode the image file, extract EXIF metadata, estimate JPEG quality.",
        "<b>Preprocess</b> — normalise dimensions and pixel values for consistent analysis.",
        "<b>Extract Residuals</b> — isolate the noise layer by subtracting a "
        "smoothed version of the image.",
        "<b>Extract Features</b> — compute six independent forensic signals from "
        "the noise residual, raw image, and metadata.",
        "<b>Score</b> — combine signals into a weighted composite score with "
        "JPEG quality attenuation, producing a label and confidence value.",
    ])
    story += [SP(8)]

    # -----------------------------------------------------------------------
    # 3. Theory
    # -----------------------------------------------------------------------
    story += H1("3. Theory & Signal Processing Background")
    story.append(PageBreak())

    story += H2("3.1  Noise Residuals")
    story.append(P(
        "A noise residual is obtained by subtracting a smooth estimate of the "
        "image from the original:"
    ))
    story.append(Paragraph(
        "    residual = original_image - smooth_filter(original_image)",
        ParagraphStyle("eq", fontName="Courier", fontSize=10, leading=14,
                       textColor=C_CODE, backColor=C_CODEBG,
                       leftIndent=20, spaceAfter=8, borderPad=6)))
    story.append(P(
        "This leaves behind only the noise layer — the part of the image that "
        "cannot be explained by the local smooth structure. Three filter types "
        "are used:"
    ))
    story += Bul([
        "<b>Wiener filter</b> (adaptive, 5x5 window) — minimises mean-squared "
        "error between filtered and original, adapting to local variance. Produces "
        "the best PRNU-style residual.",
        "<b>Gaussian filter</b> (sigma=1.0) — simple low-pass smoothing, used as "
        "a secondary residual and fallback.",
        "<b>Median filter</b> (3x3) — non-linear, robust to impulse noise, "
        "useful for detecting compression artefacts.",
    ])

    story += H2("3.2  EXIF Metadata")
    story.append(P(
        "EXIF (Exchangeable Image File Format) data is embedded by camera firmware "
        "at capture time. It contains fields that AI tools cannot replicate faithfully: "
        "camera Make and Model, lens FNumber, focal length, ISO speed, GPS coordinates, "
        "and exposure settings. Absence of these fields — or presence of only generic "
        "software tags — is a strong indicator of AI origin."
    ))
    story.append(P(
        "Scoring logic: presence of Make/Model adds 0.45; each exposure field adds 0.10 "
        "(capped at 0.25); GPS adds 0.10; FocalLength adds 0.05; any EXIF at all adds 0.15."
    ))

    story += H2("3.3  Frequency-Domain Analysis (FFT)")
    story.append(P(
        "A 2D Fast Fourier Transform (FFT) decomposes the image into its spatial "
        "frequency components. The log-magnitude spectrum reveals how energy is "
        "distributed across frequencies."
    ))
    story.append(P(
        "Camera images follow a 1/f power law with a characteristic noise floor "
        "at high frequencies (from shot noise). Diffusion models suppress high-frequency "
        "energy, producing a steeper spectral roll-off. The tool measures the fraction "
        "of total log-energy in the high-frequency band (normalised radius 0.40 – 0.50) "
        "as the spectral feature."
    ))
    story.append(P(
        "A Hann window is applied before the FFT to reduce spectral leakage "
        "from image boundary discontinuities."
    ))

    story += H2("3.4  Cross-Channel Noise Correlation")
    story.append(P(
        "Bayer demosaicing interpolates missing colour values from spatially "
        "adjacent pixels of different colours. This introduces structured "
        "cross-channel correlations in the noise residual — R, G, and B channels "
        "share noise components at neighbouring pixel positions."
    ))
    story.append(P(
        "AI generators produce colour images without this physical constraint. "
        "Their per-channel noise residuals are nearly independent. The tool computes "
        "Pearson correlation between R/G, R/B, and G/B Wiener residuals and averages "
        "them. Camera images typically show mean correlation 0.40–0.75; AI images "
        "0.05–0.30."
    ))

    story += H2("3.5  Local Variance Structure")
    story.append(P(
        "Camera shot noise follows a Poisson process: noise variance is proportional "
        "to signal level (brightness). This creates a characteristic spatial structure "
        "where brighter regions are noisier. Two sub-features are measured:"
    ))
    story += Bul([
        "<b>Coefficient of Variation (CV) of tile variances</b> — the image is "
        "divided into tiles; the standard deviation of per-tile noise variance, "
        "normalised by the mean, measures how spatially structured the noise is. "
        "Camera: CV 0.4–1.0; AI: CV 0.1–0.4.",
        "<b>Brightness-noise Pearson correlation</b> — correlation between "
        "per-tile noise variance and per-tile mean brightness. Camera: 0.2–0.7 "
        "(Poisson signature); AI: -0.2–0.2 (uncorrelated).",
    ])
    story.append(P("Final score: 0.60 * CV_score + 0.40 * correlation_score."))

    story += H2("3.6  Texture / Edge Sharpness")
    story.append(P(
        "Real lenses produce sharp, high-contrast edges due to optical physics. "
        "Diffusion models generate images with characteristically smooth textures "
        "and weaker edge gradients."
    ))
    story.append(P(
        "Sobel operators compute the horizontal and vertical gradient at each pixel. "
        "The gradient magnitude is averaged over the image and normalised by mean "
        "brightness to account for exposure differences. "
        "Camera: normalised gradient 0.30–1.00; AI: 0.10–0.40."
    ))

    story += H2("3.7  Frequency Anisotropy")
    story.append(P(
        "Natural scenes contain strong directional structures — horizontal lines "
        "from horizons, vertical lines from buildings, diagonal edges from "
        "perspective. This makes their frequency spectra <i>anisotropic</i> "
        "(energy varies strongly with angle). AI-generated images tend toward "
        "more isotropic mid-frequency distributions."
    ))
    story.append(P(
        "The mid-frequency ring (normalised radius 0.10–0.40) of the FFT spectrum "
        "is divided into 8 angular sectors. The coefficient of variation of "
        "sector energies measures anisotropy. Camera: CV 0.20–0.50; AI: 0.05–0.20."
    ))
    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # 4. Architecture & Block Diagrams
    # -----------------------------------------------------------------------
    story += H1("4. Architecture & Block Diagrams")

    story += H2("4.1  Full Processing Pipeline")

    pipeline_ascii = """\
  Input Image (JPG / PNG / WebP / BMP / TIFF)
          |
          v
  +-------------------------------------------------+
  |  LOADER  (core/loader.py)                       |
  |  - Decode file with Pillow                      |
  |  - Extract EXIF tags -> set of camera fields    |
  |  - Estimate JPEG quantisation quality (Q50-95)  |
  |  Output: image_data dict                        |
  +-------------------------------------------------+
          |
          v
  +-------------------------------------------------+
  |  PREPROCESSOR  (core/preprocess.py)             |
  |  - Resize: cap longest edge at MAX_DIMENSION    |
  |  - Convert to float32 RGB + grayscale           |
  |  - Normalise pixel values to [0, 1]             |
  |  Output: processed dict (rgb, gray, rgb_norm,   |
  |          gray_norm, sizes, flags)               |
  +-------------------------------------------------+
          |
          v
  +-------------------------------------------------+
  |  RESIDUAL EXTRACTION  (core/residual.py)        |
  |  - Wiener filter residual (PRNU-style, 5x5)     |
  |  - Gaussian filter residual (sigma=1.0)         |
  |  - Median filter residual (3x3)                 |
  |  - Per-channel Wiener (R, G, B separately)      |
  |  Output: residuals dict                         |
  +-------------------------------------------------+
          |
     +---------+-----------+
     |         |           |
  [raw img] [residuals] [EXIF data]
     |         |           |
     +---------+-----------+
          |
          v
  +-------------------------------------------------+
  |  FEATURE EXTRACTION  (core/features.py)         |
  |  6 independent signals, each -> [0, 1]          |
  |                                                 |
  |  exif_score        <- EXIF data                 |
  |  spectral_score    <- gray_norm (FFT)           |
  |  channel_cov_score <- per_channel residuals     |
  |  local_var_score   <- wiener + gray_norm        |
  |  texture_score     <- gray_norm (Sobel)         |
  |  isotropy_score    <- gray_norm (FFT sectors)   |
  |                                                 |
  |  Output: features dict (scores, details, maps)  |
  +-------------------------------------------------+
          |
          v
  +-------------------------------------------------+
  |  SCORING  (core/scoring.py)                     |
  |  - Weighted average of 6 feature scores         |
  |  - JPEG quality attenuation if Q < 70           |
  |  - Small-image attenuation if min(H,W) < 64     |
  |  - Threshold: synthetic < 0.38 / camera > 0.62  |
  |  - Confidence = distance from nearest boundary  |
  |  Output: result dict (score, label, confidence) |
  +-------------------------------------------------+
          |
     +---------+
     |         |
     v         v
  [Visuals]  [HTML Report]
  residual    report.html
  spectrum    (self-contained,
  heatmap      base64 images)
  channel_noise
"""
    story += code_block("Figure 1 — Full Processing Pipeline (ASCII)", pipeline_ascii)

    story += H2("4.2  Feature Extraction Detail")

    feat_ascii = """\
  Feature Extraction Stage
  =========================

  Input: image_data, processed, residuals
         |
         +--[EXIF data]---------> EXIF Completeness Score
         |    presence of Make, Model, GPS,
         |    exposure fields -> weighted sum -> [0,1]
         |
         +--[gray_norm]---------+ FFT with Hann window
         |                      | radial energy profile
         |                      +-> Spectral Energy Score
         |                      |   high-freq ratio [0.4-0.5 band]
         |                      |
         |                      +-> Isotropy Score
         |                          angular CV in mid ring [0.1-0.4]
         |
         +--[per_channel]-------> Channel Covariance Score
         |    Wiener residuals       Pearson corr(R,G), (R,B), (G,B)
         |    per R,G,B channel      mean abs correlation -> [0,1]
         |
         +--[wiener residual]---> Local Variance Score
         |  + [gray_norm]          tile-wise variance CV
         |                         + brightness correlation -> [0,1]
         |
         +--[gray_norm]---------+ Sobel gradient Gx, Gy
                                | grad_mag = sqrt(Gx^2 + Gy^2)
                                +-> Texture Sharpness Score
                                    norm_grad = mean(mag)/mean(gray)
"""
    story += code_block("Figure 2 — Feature Extraction Detail", feat_ascii)

    story += H2("4.3  Scoring Logic")

    scoring_ascii = """\
  Feature Scores (6 values in [0,1]):
    exif              weight = 0.20
    spectral          weight = 0.20
    channel_covariance weight = 0.20
    local_variance    weight = 0.15
    texture           weight = 0.15
    isotropy          weight = 0.10
           |
           v
  raw_score = weighted_sum / total_weight
           |
           v
  [JPEG quality < 70?]
    YES -> attenuate score toward 0.5
           raw_score = 0.5 + (raw_score - 0.5) * attenuation
           |
           v
  [Image too small? min(H,W) < 64]
    YES -> attenuate: raw_score = 0.5 + (raw_score - 0.5) * 0.5
           |
           v
  final_score = clip(raw_score, 0.0, 1.0)
           |
     +-----+-----+
     |     |     |
    <0.38 0.38 >0.62
     |   -0.62   |
     v     |     v
  SYNTH  INCONCL  CAMERA
           |
           v
  confidence = normalised distance from nearest decision boundary
"""
    story += code_block("Figure 3 — Scoring Logic", scoring_ascii)
    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # 5. Code Walkthrough
    # -----------------------------------------------------------------------
    story += H1("5. Code Walkthrough")
    story.append(P(
        "This section explains each source file, covering the purpose of "
        "every function and the reasoning behind key implementation decisions."
    ))

    # --- 5.1 config.py ---
    story += H2("5.1  config.py — Constants & Weights")
    story.append(P(
        "Central configuration file. All tunable parameters live here so they "
        "can be adjusted without touching analysis code."
    ))
    story += code_block("config.py", """\
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}
# File extensions the loader will accept.

MAX_DIMENSION = 2048
# Images larger than this are downscaled before analysis.
# Preserves forensic signals while capping memory and compute.

TILE_SIZE = 32
# Minimum tile dimension for local variance analysis.
# Smaller tiles give finer spatial resolution but more noise.

FFT_LOW_CUTOFF  = 0.10   # DC to 10% of Nyquist -> low band
FFT_MID_CUTOFF  = 0.40   # 10%-40% of Nyquist   -> mid band
# Frequency above 40% of Nyquist = high band (shot noise lives here)

SYNTHETIC_THRESHOLD = 0.38   # score < 0.38  -> label = "synthetic"
CAMERA_THRESHOLD    = 0.62   # score > 0.62  -> label = "camera"
# Zone 0.38-0.62 -> label = "inconclusive"

FEATURE_WEIGHTS = {
    "exif":               0.20,   # strongest single signal when present
    "spectral":           0.20,   # reliable across formats
    "channel_covariance": 0.20,   # strong Bayer signal
    "local_variance":     0.15,   # good but noisy on small images
    "texture":            0.15,   # format-dependent
    "isotropy":           0.10,   # supplementary
}  # weights sum to 1.0
""")

    # --- 5.2 core/utils.py ---
    story += H2("5.2  core/utils.py — Utility Functions")
    story += code_block("core/utils.py", """\
def linear_map(value, low, high):
    # Maps a scalar from [low, high] linearly to [0, 1], clamped.
    # Used by every feature function to convert raw measurements to scores.
    # The +1e-10 in the denominator prevents division-by-zero.
    return float(np.clip((value - low) / (high - low + 1e-10), 0.0, 1.0))

def safe_corrcoef(a, b):
    # Pearson correlation coefficient, guarded against degenerate input.
    # Returns 0.0 if either array has near-zero standard deviation
    # (constant arrays produce NaN from np.corrcoef).
    if np.std(a) < 1e-10 or np.std(b) < 1e-10:
        return 0.0
    result = np.corrcoef(a, b)[0, 1]
    return 0.0 if np.isnan(result) else float(result)
""")

    # --- 5.3 core/loader.py ---
    story += H2("5.3  core/loader.py — Image Loading")
    story.append(P(
        "Responsible for reading the image file from disk and extracting "
        "all metadata needed by later stages."
    ))
    story += code_block("core/loader.py — load_image()", """\
def load_image(path: str) -> dict:
    p = Path(path)
    # 1. Existence and format check — raises FileNotFoundError / ValueError early.
    suffix = p.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        raise ValueError(...)

    # 2. Decode with Pillow. img.load() forces full pixel decode before
    #    the file handle is released (avoids lazy-load issues).
    img = Image.open(p)
    img.load()

    # 3. Extract EXIF and identify which camera-specific fields are present.
    exif_data, camera_fields_found = _extract_exif(img)

    # 4. Grayscale flag — channel covariance is skipped for grayscale images.
    is_grayscale = img.mode in {"L", "1", "LA", "P"}

    # 5. JPEG quality estimation (only for .jpg/.jpeg).
    jpeg_quality = _estimate_jpeg_quality(img) if suffix in {".jpg", ".jpeg"} else None

    return { "image": img, "path": p, "format": ...,
             "exif": exif_data, "exif_camera_fields": camera_fields_found,
             "jpeg_quality": jpeg_quality, "is_grayscale": is_grayscale, ... }
""")
    story += code_block("core/loader.py — _extract_exif()", """\
def _extract_exif(img):
    # Iterates the raw EXIF tag dictionary from Pillow.
    # TAGS.get(tag_id) converts numeric tag IDs to human-readable names.
    # Bytes values are decoded to UTF-8 strings to avoid serialisation issues.
    # Returns both the full EXIF dict and the subset that matches
    # CAMERA_EXIF_FIELDS (20 camera-specific tag names).
""")
    story += code_block("core/loader.py — _estimate_jpeg_quality()", """\
def _estimate_jpeg_quality(img):
    # Reads the JPEG quantisation table (luma channel, table 0).
    # Sums all 64 coefficients: lower sum = higher quality (smaller divisors).
    # Maps the sum to approximate quality buckets: Q95 / Q85 / Q75 / Q65 / Q50.
    # This is a rough estimate; exact quality requires the original encoder settings.
    qtables = img.quantization
    q_sum = sum(qtables[0])
    # q_sum < 700  -> Q95,  < 1000 -> Q85,  < 1300 -> Q75,
    # < 1700 -> Q65,  else -> Q50
""")

    # --- 5.4 core/preprocess.py ---
    story += H2("5.4  core/preprocess.py — Preprocessing")
    story.append(P(
        "Normalises the image into a consistent representation for analysis."
    ))
    story += code_block("core/preprocess.py — preprocess()", """\
def preprocess(image_data: dict) -> dict:
    img = image_data["image"]

    # 1. Downscale if longest edge > MAX_DIMENSION (2048 px).
    #    Uses LANCZOS resampling to preserve high-frequency detail.
    #    Forensic signals are present at all scales; this caps memory usage.
    img = _resize_if_needed(img, MAX_DIMENSION)

    # 2. Force RGB conversion (handles palette, RGBA, CMYK, etc.).
    rgb_img  = img.convert("RGB")
    gray_img = rgb_img.convert("L")   # standard luminance grayscale

    # 3. Convert to float32 NumPy arrays.
    #    float32 is sufficient precision; float64 would double memory.
    rgb_array  = np.array(rgb_img,  dtype=np.float32)   # shape H x W x 3
    gray_array = np.array(gray_img, dtype=np.float32)   # shape H x W

    # 4. Normalise to [0, 1] for numerically stable feature computation.
    rgb_norm  = rgb_array  / 255.0
    gray_norm = gray_array / 255.0

    # 5. Small-image flag: images smaller than 64 px on shortest side
    #    cannot produce reliable tile-based or FFT features.
    is_small = min(gray_array.shape) < 64

    return { "rgb": rgb_array, "rgb_norm": rgb_norm,
             "gray": gray_array, "gray_norm": gray_norm,
             "is_small": is_small, ... }
""")

    # --- 5.5 core/residual.py ---
    story += H2("5.5  core/residual.py — Residual Extraction")
    story.append(P(
        "Isolates the noise layer of the image by subtracting smooth "
        "filtered versions from the original."
    ))
    story += code_block("core/residual.py — extract_residuals()", """\
def extract_residuals(processed: dict) -> dict:
    gray = processed["gray_norm"]   # grayscale, [0,1]
    rgb  = processed["rgb_norm"]    # RGB, [0,1], H x W x 3

    wiener_res   = _wiener_residual(gray)    # PRNU-style residual
    gaussian_res = _gaussian_residual(gray)  # simple high-pass
    median_res   = _median_residual(gray)    # non-linear residual

    # Per-channel Wiener residuals for cross-channel covariance analysis.
    # Computed independently per channel so cross-channel correlation
    # reflects sensor physics, not inter-channel image content.
    per_channel = np.stack(
        [_wiener_residual(rgb[:, :, c]) for c in range(3)], axis=-1
    )   # shape H x W x 3
    return { "wiener": wiener_res, "gaussian": gaussian_res,
             "median": median_res, "per_channel": per_channel }
""")
    story += code_block("core/residual.py — filter implementations", """\
def _wiener_residual(img):
    # scipy.signal.wiener() estimates the local noise variance in a 5x5
    # window and adaptively smooths accordingly.
    # NaN values (zero-variance patches) are replaced with 0.
    # Falls back to Gaussian residual on failure.
    filtered = wiener(img.astype(np.float64), mysize=5)
    filtered = np.nan_to_num(filtered, nan=0.0)
    return (img - filtered).astype(np.float32)

def _gaussian_residual(img):
    # Gaussian low-pass (sigma=1.0) is a standard high-pass pre-filter.
    filtered = gaussian_filter(img, sigma=1.0)
    return (img - filtered).astype(np.float32)

def _median_residual(img):
    # Median filter (3x3) is robust to salt-and-pepper noise and reveals
    # JPEG blocking artefacts as periodic residual patterns.
    filtered = median_filter(img, size=3)
    return (img - filtered).astype(np.float32)
""")

    story.append(PageBreak())

    # --- 5.6 core/features.py ---
    story += H2("5.6  core/features.py — Feature Extractors")
    story.append(P(
        "The most complex module. Six independent feature functions each "
        "return (score: float in [0,1], details: dict)."
    ))

    story += H3("5.6.1  extract_features() — dispatcher")
    story += code_block("", """\
def extract_features(image_data, processed, residuals) -> dict:
    # Calls each feature function and collects scores + details.
    # Graceful degradation:
    #   - is_grayscale -> channel covariance set to 0.5 (neutral)
    #   - is_small     -> local_variance and channel_cov set to 0.5
    # Returns: scores dict, details dict, maps dict (variance heatmap)
""")

    story += H3("5.6.2  _exif_score()")
    story += code_block("", """\
def _exif_score(image_data) -> (float, dict):
    # Scoring breakdown (additive):
    #   0.15  - any EXIF present at all
    #   0.45  - camera Make or Model found (strongest signal)
    #   0.10  - each exposure field (ExposureTime, FNumber, ISO, Bias)
    #           capped at 0.25 total
    #   0.10  - GPS coordinates present
    #   0.05  - FocalLength present
    # Total possible: 1.00, clipped to [0, 1]
    # Rationale: AI tools very rarely embed camera-specific EXIF.
""")

    story += H3("5.6.3  _spectral_score()")
    story += code_block("", """\
def _spectral_score(gray) -> (float, dict):
    # 1. Apply Hann window to suppress spectral leakage.
    # 2. Compute 2D FFT, shift DC to centre, take log1p of magnitude.
    # 3. Compute radial distance of each pixel from DC centre,
    #    normalised by min(height, width)/2.
    # 4. Partition into three bands:
    #      low  : norm_dist <= 0.10 (DC and very low freq)
    #      mid  : 0.10 < norm_dist <= 0.40
    #      high : 0.40 < norm_dist <= 0.50 (shot noise lives here)
    # 5. high_ratio = energy_in_high_band / total_energy
    #    -> linear_map(high_ratio, 0.05, 0.28) -> score
    # 6. Penalty: if mid band dominates over high (AI signature),
    #    apply small downward correction.
    # Camera: high_ratio ~ 0.15-0.30 | AI: high_ratio ~ 0.05-0.15
""")

    story += H3("5.6.4  _channel_covariance_score()")
    story += code_block("", """\
def _channel_covariance_score(channel_residuals) -> (float, dict):
    # channel_residuals: H x W x 3 (Wiener residuals per R, G, B)
    # Flatten each channel to 1D vectors.
    # Compute Pearson correlation for pairs: (R,G), (R,B), (G,B).
    # Take mean of absolute correlations.
    #   Camera: mean_corr ~ 0.40-0.75 (demosaicing coupling)
    #   AI:     mean_corr ~ 0.05-0.30 (independent synthesis)
    # linear_map(mean_corr, 0.05, 0.70) -> score
""")

    story += H3("5.6.5  _local_variance_score()")
    story += code_block("", """\
def _local_variance_score(residual, gray) -> (float, dict):
    # 1. Divide image into tiles of size max(TILE_SIZE, H//16) x max(TILE_SIZE, W//16).
    #    Tiles adapt to image size; minimum 2x2 tile grid required.
    # 2. Compute noise variance (np.var of Wiener residual) per tile.
    # 3. Compute mean brightness (np.mean of gray) per tile.
    # Sub-feature 1: CV = std(variances) / mean(variances)
    #   Camera: CV ~ 0.4-1.0 (spatially structured noise)
    #   AI:     CV ~ 0.1-0.4 (uniform, featureless noise)
    # Sub-feature 2: Pearson corr(variances, brightnesses)
    #   Camera: +0.2 to +0.7 (Poisson: noise scales with signal)
    #   AI:     -0.2 to +0.2 (no physical link)
    # Final: 0.60 * cv_score + 0.40 * corr_score
""")

    story += H3("5.6.6  _texture_score()")
    story += code_block("", """\
def _texture_score(gray) -> (float, dict):
    # scipy.ndimage.sobel() computes first-order gradients:
    #   Gx = sobel(gray, axis=1)   (horizontal gradient)
    #   Gy = sobel(gray, axis=0)   (vertical gradient)
    # gradient_magnitude = sqrt(Gx^2 + Gy^2) per pixel
    # normalised_gradient = mean(magnitude) / mean(brightness)
    #   Normalisation removes the effect of image exposure.
    #   Camera: 0.30-1.00 | AI: 0.10-0.40
    # linear_map(norm_grad, 0.10, 0.80) -> score
""")

    story += H3("5.6.7  _isotropy_score()")
    story += code_block("", """\
def _isotropy_score(gray) -> (float, dict):
    # 1. FFT with Hann window (same as spectral score).
    # 2. Compute radial distance map and angle map (arctan2).
    # 3. Select mid-frequency ring: 0.10 < norm_dist <= 0.40.
    # 4. Divide ring into 8 angular sectors of width pi/4.
    # 5. Mean energy per sector -> array of 8 values.
    # 6. CV of sector energies = std(energies) / mean(energies)
    #      Camera (anisotropic): CV ~ 0.20-0.50
    #      AI     (isotropic):   CV ~ 0.05-0.20
    # linear_map(cv_sectors, 0.05, 0.45) -> score
""")

    # --- 5.7 core/scoring.py ---
    story += H2("5.7  core/scoring.py — Scoring & Verdict")
    story += code_block("core/scoring.py — score_image()", """\
def score_image(features: dict) -> dict:
    # 1. Weighted average of 6 feature scores.
    #    Weights from config.FEATURE_WEIGHTS (sum = 1.0).
    #    Non-finite scores are skipped (weight excluded from denominator).
    weighted_sum = sum(score * weight for feature, weight in FEATURE_WEIGHTS)
    raw_score    = weighted_sum / total_weight

    # 2. JPEG attenuation.
    #    Low JPEG quality destroys high-frequency forensic signals.
    #    If quality < 70: pull score toward 0.5 (uncertain).
    if jpeg_quality < 70:
        raw_score = 0.5 + (raw_score - 0.5) * attenuation

    # 3. Small-image attenuation: halve the deviation from 0.5.
    if is_small:
        raw_score = 0.5 + (raw_score - 0.5) * 0.50

    # 4. Hard thresholds.
    final_score = clip(raw_score, 0.0, 1.0)
    label = "synthetic"    if final_score < 0.38 else
            "camera"       if final_score > 0.62 else
            "inconclusive"

    # 5. Confidence = normalised distance from nearest decision boundary.
    #    synthetic:    (0.38 - score) / 0.38
    #    camera:       (score - 0.62) / 0.38
    #    inconclusive: 1 - |score - 0.5| / half_zone_width
""")

    story.append(PageBreak())

    # --- 5.8 output/visualization.py ---
    story += H2("5.8  output/visualization.py — Visualisations")
    story.append(P(
        "Generates four PNG images saved to the output directory."
    ))
    story.append(feature_table([
        ["residual.png",
         "3-panel: Wiener, Gaussian, Median residuals side-by-side",
         "—", "Structured noise patches", "Uniform noise"],
        ["spectrum.png",
         "FFT log-magnitude image + radial energy profile chart",
         "—", "High flat noise floor", "Steep roll-off"],
        ["heatmap.png",
         "Local noise variance map (Gaussian-smoothed residual^2)",
         "—", "Spatially varied", "Uniform"],
        ["channel_noise.png",
         "Per-channel R, G, B Wiener residuals side-by-side",
         "—", "Visually similar pattern", "Independent patterns"],
    ]))
    story += [SP(8)]
    story.append(P(
        "All figures use Matplotlib with the non-interactive Agg backend "
        "(no display required). Images are saved at 150 DPI."
    ))

    # --- 5.9 output/report.py ---
    story += H2("5.9  output/report.py — HTML Report")
    story.append(P(
        "Generates a self-contained HTML report (report.html) with all images "
        "embedded as base64 data URIs so the file can be shared without "
        "accompanying assets."
    ))
    story += Bul([
        "<b>generate_report()</b> — orchestrates encoding and rendering.",
        "<b>_encode_original()</b> — resizes the original image to max 800 px "
        "and encodes it as base64 PNG.",
        "<b>_encode_png()</b> — reads a saved visualisation PNG and encodes it.",
        "<b>_render_html()</b> — builds the full HTML string with inline CSS, "
        "verdict box with colour coding, feature score bars, expandable "
        "technical detail sections, and a limitations warning.",
    ])

    # --- 5.10 main.py ---
    story += H2("5.10  main.py — CLI Entry Point")
    story += code_block("main.py — argument parser", """\
parser.add_argument("image")             # required positional: path to image
parser.add_argument("--output", "-o")    # root output directory
parser.add_argument("--verbose", "-v")   # print per-feature breakdown
parser.add_argument("--no-report")       # skip HTML report generation
parser.add_argument("--no-visuals")      # skip visualisation PNGs
""")
    story += code_block("main.py — execution flow", """\
1. Validate image path exists.
2. Create timestamped output directory:
       forensics_output/<stem>_YYYYMMDD_HHMMSS/
3. Run pipeline in sequence:
       load_image -> preprocess -> extract_residuals
       -> extract_features -> score_image
4. Generate visualisations (unless --no-visuals).
5. Generate HTML report (unless --no-report).
6. Print verdict box to terminal.
7. Return exit code 0 (success), 1 (file error), 2 (pipeline error).
""")
    story.append(P(
        "The main() function accepts an optional argv list for testability "
        "(allows calling main(['test.jpg', '--verbose']) from tests). "
        "Visualisation and report failures are caught and printed as warnings "
        "rather than aborting the analysis result."
    ))

    # --- 5.11 tests/test_basic.py ---
    story += H2("5.11  tests/test_basic.py — Test Suite")
    story.append(P(
        "12 pytest tests covering the full pipeline and edge cases. "
        "No real images are required — synthetic test images are "
        "generated in memory."
    ))
    story.append(info_table([
        ("_make_noisy_image()",
         "Builds a camera-like 256x256 image with sharp grid edges (anisotropic "
         "spectrum), shared shot noise scaled by brightness, and cross-channel "
         "correlated noise from a common base."),
        ("_make_smooth_image()",
         "Builds an AI-like 256x256 smooth gradient with tiny, independent "
         "per-channel noise. No structural edges, isotropic noise."),
        ("test_full_pipeline_noisy/smooth",
         "Smoke tests: run full pipeline, assert score in [0,1] and label is valid."),
        ("test_small_image_does_not_crash",
         "32x32 image — verifies small-image guards work."),
        ("test_grayscale_image_does_not_crash",
         "128x128 grayscale — verifies channel covariance skip."),
        ("test_feature_scores_bounded",
         "Asserts all 6 feature scores are in [0, 1]."),
        ("test_noisy_scores_higher_than_smooth",
         "Ordering test: camera-like image must score >= AI-like image - 0.02."),
        ("test_linear_map_clamps",
         "Unit test: linear_map returns 0 below low, 1 above high, 0.5 at midpoint."),
        ("test_safe_corrcoef_constant / perfect",
         "Unit tests: corrcoef returns 0 for constant arrays, 1 for identical arrays."),
        ("test_loader_missing_file",
         "FileNotFoundError raised for non-existent path."),
        ("test_loader_unsupported_format",
         "ValueError raised for .xyz extension."),
        ("test_loader_returns_required_keys",
         "All required keys present in image_data dict."),
    ], col_widths=[5*cm, PAGE_W - 2*MARGIN - 5*cm]))
    story.append(PageBreak())

    # -----------------------------------------------------------------------
    # 6. Limitations
    # -----------------------------------------------------------------------
    story += H1("6. Limitations")
    lim_data = [
        ["Limitation", "Impact", "Mitigation"],
        ["Social media recompression\n(Twitter/X, Instagram, WhatsApp)",
         "Strips EXIF, re-encodes JPEG, destroys high-frequency signals",
         "JPEG quality attenuation in scoring"],
        ["JPEG quality < 70",
         "Destroys noise floor and cross-channel correlations",
         "Automatic confidence attenuation"],
        ["Post-processing\n(sharpen, denoise, upscale, colour grade)",
         "Can make AI appear camera-like or vice versa",
         "Multi-residual approach partially mitigates"],
        ["Screenshots of AI images",
         "Desktop rendering adds noise mimicking camera noise",
         "Flag in report (Phase 2)"],
        ["Adversarial perturbations",
         "Imperceptible noise can flip any heuristic detector",
         "Out of scope for heuristic phase"],
        ["Printed + re-photographed AI images",
         "Acquire real sensor noise — will appear authentic",
         "Unsolvable without scene context"],
        ["No calibration dataset",
         "Thresholds 0.38 / 0.62 are heuristic, not ROC-optimal",
         "Phase 3 ML calibration"],
        ["Modern AI image quality\n(SD3, DALL-E 3, Flux)",
         "Increasingly realistic; signals weaker",
         "Phase 3 ML classifier required"],
    ]
    lim_t = Table(
        [[Paragraph(cell, styles["body_left"]) for cell in row] for row in lim_data],
        colWidths=[4.5*cm, 5.5*cm, 5.5*cm]
    )
    lim_t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), C_DARK),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, C_SILVER]),
        ("GRID", (0,0), (-1,-1), 0.4, colors.HexColor("#cccccc")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(lim_t)
    story += [SP(10)]

    # -----------------------------------------------------------------------
    # 7. Roadmap
    # -----------------------------------------------------------------------
    story += H1("7. Roadmap")
    story.append(info_table([
        ("Phase 1 (Complete)",
         "Heuristic signal-processing pipeline: 6 features, CLI, HTML report, 12 tests."),
        ("Phase 2 (Planned)",
         "DWT residuals, snap-back SSIM, chroma analysis, noise autocorrelation, "
         "partial manipulation localisation, calibrated thresholds from reference dataset."),
        ("Phase 3 (Future)",
         "ML classifier (Random Forest / XGBoost) trained on 5,000+ real + 5,000+ AI "
         "images with Platt-scaled probabilities. Diffusion Noise Feature (DNF) partial "
         "inversion. AUC-ROC evaluation. Cross-model generalisation tests."),
        ("Phase 4 (Stretch)",
         "GUI (Tkinter/Qt), batch mode, FastAPI web endpoint, Docker container."),
    ]))
    story += [SP(10)]

    # -----------------------------------------------------------------------
    # 8. References
    # -----------------------------------------------------------------------
    story += H1("8. References")
    refs = [
        ("[1] Frank, J. et al. — \"Leveraging Frequency Analysis for Deep Fake Image "
         "Recognition.\" International Conference on Machine Learning (ICML), 2020. "
         "Establishes FFT-based artifact detection for GAN-generated images."),
        ("[2] Guan, Z. et al. — \"Noise-Informed Diffusion-Generated Image Detection "
         "with Anomaly Attention.\" IEEE Transactions on Information Forensics and "
         "Security (TIFS), 2025. Basis for cross-channel noise correlation feature."),
        ("[3] Yang, X. — \"FreqCross: Multi-Modal Frequency-Spatial Fusion Network.\" "
         "arXiv:2507.02995, 2025. Identifies 0.10-0.40 normalised frequency band as "
         "discriminative; informs spectral score band boundaries."),
        ("[4] Ameen, M. and Islam, M. — \"Detecting AI-Generated Images via Diffusion "
         "Snap-Back Reconstruction.\" arXiv:2511.00352, 2025. Snap-back SSIM method "
         "planned for Phase 2."),
        ("[5] Zhang, W. and Xu, S. — \"Diffusion Noise Feature.\" ECAI 2025. "
         "Partial inverse diffusion amplifies AI fingerprints; targeted for Phase 3."),
        ("[6] Mavali, E. et al. — \"Fake It Until You Break It: Adversarial Robustness "
         "of AI-Generated Image Detectors.\" arXiv:2410.01574, 2024. Adversarial "
         "stress testing framework referenced in Phase 3 robustness plan."),
        ("[7] Yan, Z. et al. — \"Dual Frequency Branch Framework with DWT + FFT Phase.\" "
         "IEEE TIFS, 2025. arXiv:2501.15253. DWT+FFT phase combination targeted for "
         "Phase 2 residual improvements."),
        ("[8] Kirchner, M. and Bohme, R. — \"SPN-based Camera Attribution and the "
         "Forensic Analysis of PRNU.\" IEEE Signal Processing Letters, 2010. "
         "Theoretical foundation for PRNU-style Wiener residual extraction."),
        ("[9] Chen, M. et al. — \"Determining Image Origin and Integrity Using Sensor "
         "Noise.\" IEEE TIFS, 2008. Seminal PRNU paper establishing the Wiener filter "
         "approach for sensor fingerprinting."),
    ]
    for ref in refs:
        story.append(Paragraph(ref, ParagraphStyle(
            "ref", fontName="Helvetica", fontSize=9.5, leading=14,
            textColor=C_DARK, leftIndent=20, firstLineIndent=-20,
            spaceAfter=8, alignment=TA_JUSTIFY)))

    story += [SP(20)]
    story.append(HRFlowable(width="100%", thickness=1, color=C_SILVER, spaceAfter=10))
    story.append(Paragraph(
        "Image Noise Forensics Tool  ·  Phase 1 Technical Report  ·  Heuristic analysis only — not for evidentiary use",
        ParagraphStyle("footer", fontName="Helvetica-Oblique", fontSize=8,
                       textColor=C_GREY, alignment=TA_CENTER)))

    return story


# ---------------------------------------------------------------------------
# Page template with header/footer
# ---------------------------------------------------------------------------

def on_page(canvas, doc):
    canvas.saveState()
    w, h = A4
    # Header bar
    canvas.setFillColor(C_DARK)
    canvas.rect(MARGIN, h - 1.4*cm, w - 2*MARGIN, 0.6*cm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(MARGIN + 4, h - 1.4*cm + 8, "Image Noise Forensics Tool — Technical Report")
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(w - MARGIN - 4, h - 1.4*cm + 8, f"Page {doc.page}")
    # Footer line
    canvas.setStrokeColor(C_SILVER)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, 1.5*cm, w - MARGIN, 1.5*cm)
    canvas.setFillColor(C_GREY)
    canvas.setFont("Helvetica-Oblique", 7.5)
    canvas.drawCentredString(w/2, 0.9*cm,
        "Heuristic analysis only — not for evidentiary use")
    canvas.restoreState()


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

def main():
    doc = SimpleDocTemplate(
        OUTPUT_FILE,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=2.4*cm,
        bottomMargin=2.4*cm,
        title="Image Noise Forensics Tool — Technical Project Report",
        author="Deepfake-Detector Project",
        subject="Camera vs AI-Generated Image Detection",
    )
    story = build_story()
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    print(f"PDF written to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

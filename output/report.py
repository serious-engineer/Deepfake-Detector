import base64
import io
from datetime import datetime
from pathlib import Path

from PIL import Image


_FEATURE_LABELS = {
    "exif":               "EXIF Metadata Completeness",
    "spectral":           "High-Frequency Spectral Energy",
    "channel_covariance": "Cross-Channel Noise Correlation",
    "local_variance":     "Local Noise Variance Structure",
    "texture":            "Edge / Texture Sharpness",
    "isotropy":           "Frequency-Domain Anisotropy",
}

_FEATURE_DESCRIPTIONS = {
    "exif": (
        "Presence of camera-specific EXIF fields (Make, Model, ISO, GPS, …). "
        "AI-generated images rarely carry real camera EXIF."
    ),
    "spectral": (
        "Ratio of high-frequency energy in the FFT spectrum. Camera images retain "
        "sensor shot noise at high frequencies; diffusion models suppress it."
    ),
    "channel_covariance": (
        "Pearson correlation of Wiener noise residuals across R/G/B channels. "
        "Bayer demosaicing in cameras creates strong cross-channel correlations "
        "absent in AI output."
    ),
    "local_variance": (
        "Coefficient of variation of per-tile noise variance + correlation with "
        "local brightness. Camera shot noise (Poisson) scales with signal level."
    ),
    "texture": (
        "Normalised Sobel gradient magnitude. Real optics produce sharp, "
        "high-contrast edges; diffusion models generate characteristically smooth textures."
    ),
    "isotropy": (
        "Angular coefficient of variation in the mid-frequency ring of the FFT. "
        "Natural scenes are anisotropic (edges, lines); AI images tend toward "
        "isotropic frequency distributions."
    ),
}


def generate_report(
    image_data: dict,
    processed: dict,
    features: dict,
    result: dict,
    out_dir: Path,
) -> None:
    out_dir = Path(out_dir)

    orig_b64 = _encode_original(image_data["path"])
    vis = {name: _encode_png(out_dir / f"{name}.png")
           for name in ("residual", "spectrum", "heatmap", "channel_noise")}

    html = _render_html(image_data, processed, features, result, orig_b64, vis)

    (out_dir / "report.html").write_text(html, encoding="utf-8")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _encode_original(path: Path, max_px: int = 800) -> str:
    try:
        img = Image.open(path).convert("RGB")
        img.thumbnail((max_px, max_px), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


def _encode_png(path: Path) -> str:
    if path.exists():
        return base64.b64encode(path.read_bytes()).decode()
    return ""


def _img_tag(b64: str, mime: str = "image/png", style: str = "") -> str:
    if not b64:
        return "<p style='color:#999;font-style:italic'>Image not available</p>"
    return f'<img src="data:{mime};base64,{b64}" style="{style}">'


# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------

def _render_html(
    image_data: dict,
    processed: dict,
    features: dict,
    result: dict,
    orig_b64: str,
    vis: dict[str, str],
) -> str:
    label = result["label"]
    score = result["score"]
    confidence = result["confidence"]
    feature_scores = result["feature_scores"]

    _VERDICT_STYLE = {
        "camera":       ("#1e6f45", "#d4edda", "CAMERA"),
        "synthetic":    ("#842029", "#f8d7da", "SYNTHETIC  (AI-GENERATED)"),
        "inconclusive": ("#664d03", "#fff3cd", "INCONCLUSIVE"),
    }
    border_col, bg_col, label_text = _VERDICT_STYLE[label]

    score_pct = int(score * 100)
    conf_pct = f"{confidence:.1%}"

    # Feature score rows
    feat_rows = ""
    for name, val in feature_scores.items():
        pct = int(val * 100)
        bar_col = "#1e6f45" if val > 0.62 else ("#842029" if val < 0.38 else "#e9a100")
        desc = _FEATURE_DESCRIPTIONS.get(name, "")
        label_str = _FEATURE_LABELS.get(name, name)
        feat_rows += f"""
        <tr>
          <td style="padding:10px 12px;vertical-align:top">
            <div style="font-weight:600;margin-bottom:3px">{label_str}</div>
            <div style="font-size:11px;color:#666">{desc}</div>
          </td>
          <td style="padding:10px 12px;vertical-align:middle;width:45%">
            <div style="background:#e0e0e0;border-radius:4px;height:14px;overflow:hidden">
              <div style="background:{bar_col};width:{pct}%;height:100%"></div>
            </div>
          </td>
          <td style="padding:10px 12px;text-align:right;font-family:monospace;
                     vertical-align:middle;font-weight:700;color:{bar_col}">{val:.3f}</td>
        </tr>"""

    # Technical detail tables
    detail_html = ""
    for fname, ddict in features["details"].items():
        rows = ""
        for k, v in ddict.items():
            if isinstance(v, float):
                vstr = f"{v:.5f}"
            elif isinstance(v, list):
                vstr = ", ".join(f"{x:.5f}" if isinstance(x, float) else str(x) for x in v[:8])
            else:
                vstr = str(v)
            rows += (
                f"<tr><td style='padding:4px 10px;color:#555;width:50%'>{k}</td>"
                f"<td style='padding:4px 10px;font-family:monospace'>{vstr}</td></tr>"
            )
        detail_html += f"""
        <details style="margin-bottom:10px">
          <summary style="cursor:pointer;font-weight:600;padding:6px 0">
            {_FEATURE_LABELS.get(fname, fname)}
          </summary>
          <table style="width:100%;font-size:12px;border-collapse:collapse;margin-top:6px">{rows}</table>
        </details>"""

    # Metadata grid
    img_w, img_h = processed["original_size"]
    exif = image_data["exif"]
    meta_items = [
        ("File", image_data["path"].name),
        ("Format", image_data["format"]),
        ("Dimensions", f"{img_w} × {img_h} px"),
        ("Colour Mode", image_data["mode"]),
        ("JPEG Quality (est.)", image_data["jpeg_quality"] or "N/A"),
        ("EXIF Fields", f"{len(exif)} found"),
        ("Camera Make", exif.get("Make") or "—"),
        ("Camera Model", exif.get("Model") or "—"),
    ]
    meta_html = "".join(
        f"<div class='meta-item'><span class='mk'>{k}</span><span>{v}</span></div>"
        for k, v in meta_items
    )

    # Visualisation panels
    def vis_card(key: str, caption: str) -> str:
        return (
            f"<div class='vis-card'>"
            f"{_img_tag(vis[key], style='width:100%;height:auto;display:block')}"
            f"<p>{caption}</p></div>"
        )

    ts = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Forensics Report — {image_data['path'].name}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
        background:#f0f2f5;color:#222;line-height:1.5}}
  .wrap{{max-width:1100px;margin:0 auto;padding:28px 20px}}
  .card{{background:#fff;border-radius:10px;padding:22px 24px;margin-bottom:20px;
         box-shadow:0 1px 6px rgba(0,0,0,.08)}}
  h1{{font-size:20px;font-weight:800;color:#111}}
  h2{{font-size:15px;font-weight:700;margin-bottom:14px;padding-bottom:8px;
      border-bottom:2px solid #f0f0f0;color:#333}}
  .verdict-box{{background:{bg_col};border:2px solid {border_col};border-radius:10px;
                padding:24px;margin-bottom:20px;text-align:center}}
  .verdict-label{{font-size:26px;font-weight:900;letter-spacing:3px;color:{border_col}}}
  .score-bar{{background:#e0e0e0;border-radius:8px;height:10px;margin:14px 0 4px;
               overflow:hidden}}
  .score-fill{{background:linear-gradient(90deg,#842029,#e9a100,#1e6f45);
               height:100%;width:{score_pct}%}}
  .score-legend{{display:flex;justify-content:space-between;font-size:11px;color:#888}}
  .meta-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:8px}}
  .meta-item{{background:#f8f9fa;border-radius:6px;padding:8px 12px;font-size:13px;
              display:flex;flex-direction:column;gap:2px}}
  .mk{{font-weight:600;font-size:11px;color:#888;text-transform:uppercase;letter-spacing:.5px}}
  .vis-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:14px}}
  .vis-card{{border:1px solid #e8e8e8;border-radius:8px;overflow:hidden}}
  .vis-card p{{padding:8px 12px;font-size:12px;color:#666;text-align:center;background:#fafafa}}
  .warning{{background:#fff8e1;border-left:4px solid #f9a825;padding:14px 18px;
             border-radius:4px;font-size:13px}}
  .warning ul{{margin-top:8px;padding-left:20px}}
  .warning li{{margin-bottom:4px}}
  table{{width:100%;border-collapse:collapse}}
  tr:nth-child(even) td{{background:#f8f9fa}}
  details summary{{user-select:none}}
  details summary:hover{{color:#1a73e8}}
</style>
</head>
<body>
<div class="wrap">

  <div style="margin-bottom:22px">
    <h1>Image Noise Forensics Report</h1>
    <p style="color:#888;font-size:13px;margin-top:4px">
      Generated: {ts} &nbsp;·&nbsp; File: {image_data['path'].name}
    </p>
  </div>

  <!-- Verdict -->
  <div class="verdict-box">
    <div class="verdict-label">{label_text}</div>
    <div class="score-bar"><div class="score-fill"></div></div>
    <div class="score-legend"><span>← SYNTHETIC (0.0)</span><span>CAMERA (1.0) →</span></div>
    <div style="margin-top:12px;font-size:15px">
      Composite score: <strong>{score:.3f}</strong>
      &nbsp;·&nbsp;
      Confidence: <strong>{conf_pct}</strong>
    </div>
    <div style="margin-top:6px;font-size:12px;color:{border_col};opacity:.75">
      Inconclusive zone: 0.38 – 0.62 &nbsp;·&nbsp;
      Synthetic: &lt; 0.38 &nbsp;·&nbsp; Camera: &gt; 0.62
    </div>
  </div>

  <!-- Image info -->
  <div class="card">
    <h2>Image Information</h2>
    <div class="meta-grid">{meta_html}</div>
  </div>

  <!-- Feature scores -->
  <div class="card">
    <h2>Feature Scores
      <span style="font-weight:400;font-size:12px;color:#888;margin-left:8px">
        0.0 = synthetic · 1.0 = camera
      </span>
    </h2>
    <table>
      <thead>
        <tr style="font-size:11px;color:#999;background:#f8f9fa">
          <th style="padding:8px 12px;text-align:left;font-weight:600">Feature</th>
          <th style="padding:8px 12px;text-align:left;font-weight:600">Score</th>
          <th style="padding:8px 12px;text-align:right;font-weight:600">Value</th>
        </tr>
      </thead>
      <tbody>{feat_rows}</tbody>
    </table>
  </div>

  <!-- Original image -->
  <div class="card">
    <h2>Original Image</h2>
    <div style="text-align:center">
      {_img_tag(orig_b64, style='max-width:640px;max-height:480px;border-radius:6px;'
                                'box-shadow:0 2px 10px rgba(0,0,0,.15)')}
    </div>
  </div>

  <!-- Visualisations -->
  <div class="card">
    <h2>Forensic Visualisations</h2>
    <div class="vis-grid">
      {vis_card("residual",     "Noise Residuals — Wiener / Gaussian / Median")}
      {vis_card("spectrum",     "FFT Magnitude Spectrum + Radial Energy Profile")}
      {vis_card("heatmap",      "Local Noise Variance Heatmap")}
      {vis_card("channel_noise","Per-Channel Noise Residuals (R · G · B)")}
    </div>
  </div>

  <!-- Technical details -->
  <div class="card">
    <h2>Technical Details</h2>
    {detail_html}
  </div>

  <!-- Limitations -->
  <div class="card">
    <h2>Limitations &amp; Caveats</h2>
    <div class="warning">
      <strong>This tool produces heuristic estimates — not definitive verdicts.</strong>
      <ul>
        <li><strong>Social-media recompression</strong> (Twitter/X, Instagram, WhatsApp) degrades
            high-frequency forensic signals; results on downloaded images may be unreliable.</li>
        <li><strong>JPEG compression</strong> below Q70 destroys the noise patterns this tool
            relies on; confidence is automatically attenuated for low-quality JPEG.</li>
        <li><strong>Post-processing</strong> (sharpening, denoising, upscaling, colour grading)
            can make AI images appear camera-like and vice-versa.</li>
        <li><strong>Screenshots</strong> of AI-generated images introduce rendering noise that
            mimics camera noise patterns.</li>
        <li><strong>Adversarial perturbations</strong> — imperceptible noise added intentionally
            — can flip any heuristic detector.</li>
        <li><strong>Printed &amp; re-photographed AI images</strong> acquire real sensor noise and
            will appear authentic to this tool.</li>
        <li><strong>Absence of synthetic signals ≠ proof of authenticity.</strong></li>
        <li>Scoring thresholds are calibrated heuristically; confidence values are
            relative indicators, not calibrated probabilities.</li>
      </ul>
    </div>
  </div>

  <div style="text-align:center;color:#bbb;font-size:11px;padding:20px 0">
    Image Noise Forensics Tool · heuristic analysis only · not for evidentiary use
  </div>

</div>
</body>
</html>"""

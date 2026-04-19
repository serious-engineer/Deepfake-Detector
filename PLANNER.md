# Image Noise Forensics Tool — Project Planner

## Status Legend
- [x] Done
- [-] In progress
- [ ] Not started

---

## Folder Structure

```
Deepfake-Detector/
├── main.py               # CLI entry point
├── config.py             # Thresholds, weights, constants
├── requirements.txt
├── README.md
├── PLANNER.md
├── .gitignore
│
├── core/
│   ├── __init__.py
│   ├── loader.py         # Image loading + EXIF extraction
│   ├── preprocess.py     # Normalisation, resize
│   ├── residual.py       # Wiener / Gaussian / Median residuals
│   ├── features.py       # 6 forensic feature extractors
│   ├── scoring.py        # Weighted aggregation, label assignment
│   └── utils.py          # linear_map, safe_corrcoef
│
├── output/
│   ├── __init__.py
│   ├── visualization.py  # matplotlib figure generation
│   └── report.py         # Self-contained HTML report
│
├── tests/
│   ├── __init__.py
│   └── test_basic.py     # 12 pytest tests
│
└── input/                # gitignored — place local images here
    └── Dataset/
        ├── Train/
        │   └── Fake/
        └── Test/
            ├── Fake/
            └── Real/
```

---

## Phase 1 — MVP (Complete)

### Core Pipeline
- [x] Image loader with EXIF extraction and JPEG quality estimation
- [x] Preprocessor (RGB/grayscale normalisation, downscale guard)
- [x] Wiener filter residual extraction (PRNU-style)
- [x] Gaussian + Median filter residuals (secondary)
- [x] Per-channel noise residuals for covariance analysis

### Features
- [x] EXIF completeness score (camera Make/Model/GPS/exposure fields)
- [x] Radial spectral energy distribution (FFT, 0.1–0.4 band analysis)
- [x] Cross-channel noise correlation (Bayer demosaicing proxy)
- [x] Local variance structure (shot noise CV + brightness correlation)
- [x] Texture/edge sharpness (normalised Sobel gradient)
- [x] Frequency-domain anisotropy (angular CV in mid-frequency ring)

### Output
- [x] residual.png — Wiener / Gaussian / Median residuals
- [x] spectrum.png — FFT log-spectrum + radial energy profile
- [x] heatmap.png — local noise variance heatmap
- [x] channel_noise.png — per-channel R/G/B noise residuals
- [x] report.html — self-contained HTML report (base64 embedded images)

### Infrastructure
- [x] CLI (argparse): `python main.py image.jpg --verbose`
- [x] JPEG quality confidence attenuation
- [x] Small-image guard
- [x] Grayscale image guard (skips channel covariance)
- [x] 12 pytest unit/integration tests

---

## Phase 2 — Better Features (Planned)

### Residuals
- [ ] **Discrete Wavelet Transform (DWT) residual** using PyWavelets
  - DWT+FFT phase combination outperforms FFT alone (IEEE TIFS 2025)
  - Target: replace or supplement Gaussian residual
- [ ] **Multi-scale noise pyramid** — 3 octaves, detect scale-specific artifacts

### Features
- [ ] **Snap-back perceptual similarity** — apply mild bilateral denoising, measure SSIM/PSNR change
  - Real images are more robust to mild denoising (Snap-Back paper 2025)
- [ ] **Block artifact map** — detect 8×8 DCT periodicity *only* when JPEG confirmed
  - Current implementation skipped because JPEG-compressed AI images show identical artifacts
- [ ] **Chroma channel analysis** — separate Cb/Cr from YCbCr; camera sensors have distinct chroma noise
- [ ] **Noise autocorrelation** — camera PRNU produces characteristic spatial autocorrelation peaks
- [ ] **Color space cross-analysis** — LAB a*/b* channels expose AI color distribution anomalies

### Scoring
- [ ] **Calibrated thresholds** — collect reference set (≥200 real camera + ≥200 AI images per model)
  - Current thresholds (0.38/0.62) are heuristic; replace with ROC-optimal thresholds
- [ ] **Per-format adjustments** — PNG vs JPEG vs WebP have different baseline forensic profiles
- [ ] **Partial manipulation detection** — localize suspicious regions rather than single verdict

---

## Phase 3 — ML Enhancement (Future)

### Dataset
- [ ] Collect balanced dataset: real camera (RAISE, Dresden, MIT FiveK) vs AI-generated
  - Sources: Stable Diffusion 3.5, DALL-E 3, Midjourney v6, Flux
  - Target: 5,000 real + 5,000 synthetic, varied JPEG qualities
- [ ] Augmentation pipeline: JPEG compression Q50–95, resize, mild sharpening, screenshot simulation

### Model
- [ ] **Feature-based ML classifier** — train Random Forest / XGBoost on Phase 1+2 features
  - Apply Platt scaling or isotonic regression for calibrated probabilities
  - Replace heuristic confidence with real probability estimates
- [ ] **Diffusion Noise Feature (DNF)** — partial inverse diffusion using a small pre-trained model
  - Amplifies high-frequency artifacts as AI fingerprints (DNF paper, ECAI 2025)
- [ ] **Evaluation** — AUC-ROC, F1, accuracy on held-out set; test at JPEG Q50/70/90

### Robustness
- [ ] **Adversarial stress tests** — add Gaussian noise (σ=0.05), mild blur, JPEG Q70 to AI images
- [ ] **Cross-model generalization** — test classifier trained on SD3.5 against DALL-E 3 images

---

## Phase 4 — UX / Distribution (Stretch)

- [ ] GUI wrapper (Tkinter or Qt) with drag-and-drop
- [ ] Side-by-side comparison mode
- [ ] Batch mode: `python main.py folder/ --batch`
- [ ] Web API (FastAPI) — `POST /analyse` returns JSON result
- [ ] Docker container for deployment
- [ ] Confidence calibration dashboard

---

## Known Limitations (must stay in README and report)

| Limitation | Impact | Mitigation |
|---|---|---|
| Social media recompression | Destroys high-frequency signals | JPEG quality attenuation in scoring |
| No calibration dataset | Thresholds are heuristic | Phase 3 ML |
| Adversarial perturbations | Can flip any heuristic | Out of scope for heuristic phase |
| Printed + re-photographed AI | Gains real sensor noise | Unsolvable without scene context |
| Post-processing (sharpen/denoise) | Mimics or destroys forensic patterns | Partial: multi-residual approach |
| Screenshot of AI image | Adds desktop rendering noise | Flag in report |
| Modern AI image quality | SD3/DALL-E3 increasingly realistic | Phase 3 ML required |

---

## Research Papers (Implementation Priority)

| Priority | Paper | Phase |
|---|---|---|
| Done | Frank et al. (ICML 2020) — FFT artifacts in GANs | 1 |
| Done | FreqCross (2025) — 0.1–0.4 band signatures | 1 |
| Done | NASA / IEEE TIFS (2025) — cross-channel noise | 1 |
| Phase 2 | Snap-Back Reconstruction (arXiv 2511.00352) | 2 |
| Phase 2 | Dual Frequency Branch DWT+FFT (arXiv 2501.15253) | 2 |
| Phase 3 | DNF — Diffusion Noise Feature (arXiv 2312.02625) | 3 |
| Phase 3 | PiN-CLIP (arXiv 2511.16136) — noise augmentation | 3 |
| Background | Methods & Trends Survey (arXiv 2502.15176) | — |

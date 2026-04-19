# Cy3b–ATTO647N Pairing and Orientation Analysis Pipeline

## Overview

This script performs spatial pairing and geometric analysis of two single-molecule localization microscopy (SMLM) datasets:

- **Cy3b (C1, TIRF 560 channel)** — green fluorophores  
- **ATTO647N (C2, TIRF 647 channel)** — red fluorophores  

The pipeline:

1. Identifies spatially correlated fluorophore pairs
2. Computes inter-particle distance
3. Calculates azimuthal (φ) and tilt (θ) angles
4. Applies quality filtering (thresholding)
5. Generates visualization plots
6. Exports results to an Excel file

---

## Input Files

The script requires two CSV files:

- `Cy3b.csv`
- `ATTO647N.csv`

Each file must contain the following columns:

| Column Name | Description |
|------------|------------|
| `id` | Unique localization ID |
| `frame` | Frame number |
| `x [nm]` | X coordinate (nanometers) |
| `y [nm]` | Y coordinate (nanometers) |
| `intensity [photon]` | Photon count (signal intensity) |
| `uncertainty_xy [nm]` | Localization precision |

These formats are consistent with outputs from ThunderSTORM (Ovesný et al., 2014).

---

## Section 1 — Pairing Algorithm

### Method

For each Cy3b localization:

- A KD-tree is used to search for ATTO647N points within a radius of **232 nm**
- Matching is performed **per frame**

### Matching Rules

| Condition | Action |
|----------|-------|
| No ATTO point within radius | Discard |
| More than one ATTO point | Discard (ambiguous) |
| Exactly one ATTO point | Accept as valid pair |

KD-tree implementation improves computational efficiency (Bentley, 1975).

---

## Geometric Calculations

### Distance

\[
d = \sqrt{(x_2 - x_1)^2 + (y_2 - y_1)^2}
\]

### Azimuthal Angle (φ)

\[
\phi = \tan^{-1}\left(\frac{dy}{dx}\right)
\]

- Converted to degrees
- Range: 0–360°

### Tilt Angle (θ)

\[
\theta = \cos^{-1}\left(\frac{d}{L}\right)
\]

Where:

- \(L = 120 \, \text{nm}\) (rod length)

This assumes a rigid rod projection model (Bustamante et al., 1994).

---

## Output File

The script generates:




### Sheet: `Paired_Results`

Contains:

- Original Cy3b and ATTO647N data
- Displacement vectors (`dx`, `dy`)
- Distance (nm)
- Azimuthal angle (deg)
- Tilt angle (deg)

---

## Section 2 — Thresholding

Filtering is applied to remove low-quality localizations.

### Adjustable Parameters

```python
CY3B_INTENSITY_MIN = 100
CY3B_INTENSITY_MAX = 2000
CY3B_UNCERTAINTY_MAX = 40

ATTO_INTENSITY_MIN = 100
ATTO_INTENSITY_MAX = 2000
ATTO_UNCERTAINTY_MAX = 40
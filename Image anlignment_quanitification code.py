# ======================================================================================
# SECTION 1 — PAIRING ANALYSIS + OUTPUT FILE
# ======================================================================================

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

# --------------------------------------------------------------------------------------
# FILE NAMES
# --------------------------------------------------------------------------------------
CY3B_FILE = "Cy3b.csv"
ATTO_FILE = "ATTO647N.csv"

# --------------------------------------------------------------------------------------
# PARAMETERS
# --------------------------------------------------------------------------------------
RADIUS_NM = 232.0
ROD_LENGTH_NM = 120.0

ID_COL = "id"
FRAME_COL = "frame"
XCOL = "x [nm]"
YCOL = "y [nm]"

# --------------------------------------------------------------------------------------
# TIMESTAMP
# --------------------------------------------------------------------------------------
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_FILE = f"Cy3b_ATTO647N_paired_analysis_{ts}.xlsx"

# --------------------------------------------------------------------------------------
# LOAD DATA
# --------------------------------------------------------------------------------------
df_cy3b = pd.read_csv(CY3B_FILE)
df_atto = pd.read_csv(ATTO_FILE)

# Preserve all columns using prefixes
cy3b_pref = df_cy3b.add_prefix("Cy3b_")
atto_pref = df_atto.add_prefix("ATTO647N_")

# --------------------------------------------------------------------------------------
# BUILD KD-TREES PER FRAME
# --------------------------------------------------------------------------------------
atto_groups = {}
atto_trees = {}

for frame_value, group in atto_pref.groupby(f"ATTO647N_{FRAME_COL}"):
    group = group.reset_index(drop=True)
    atto_groups[frame_value] = group
    atto_trees[frame_value] = cKDTree(
        group[[f"ATTO647N_{XCOL}", f"ATTO647N_{YCOL}"]].to_numpy(dtype=float)
    )

# --------------------------------------------------------------------------------------
# MATCHING LOGIC
# --------------------------------------------------------------------------------------
rows_out = []
discarded_cy3b = []
discarded_atto = set()

for idx, cy3b_row in cy3b_pref.iterrows():
    frame = cy3b_row[f"Cy3b_{FRAME_COL}"]

    if frame not in atto_trees:
        continue

    tree = atto_trees[frame]
    group = atto_groups[frame]

    cy3b_xy = [cy3b_row[f"Cy3b_{XCOL}"], cy3b_row[f"Cy3b_{YCOL}"]]
    neighbors = tree.query_ball_point(cy3b_xy, r=RADIUS_NM)

    # no match
    if len(neighbors) == 0:
        continue

    # ambiguous → delete all
    if len(neighbors) > 1:
        discarded_cy3b.append(idx)
        for j in neighbors:
            key = (
                group.loc[j, f"ATTO647N_{FRAME_COL}"],
                group.loc[j, f"ATTO647N_{ID_COL}"]
            )
            discarded_atto.add(key)
        continue

    # exactly one match
    j = neighbors[0]
    atto_row = group.loc[j]

    key = (
        atto_row[f"ATTO647N_{FRAME_COL}"],
        atto_row[f"ATTO647N_{ID_COL}"]
    )

    if key in discarded_atto:
        continue

    dx_raw = atto_row[f"ATTO647N_{XCOL}"] - cy3b_row[f"Cy3b_{XCOL}"]
    dy_raw = atto_row[f"ATTO647N_{YCOL}"] - cy3b_row[f"Cy3b_{YCOL}"]

    distance = np.sqrt(dx_raw**2 + dy_raw**2)
    azimuth = (np.degrees(np.arctan2(dy_raw, dx_raw)) + 360) % 360

    ratio = np.clip(distance / ROD_LENGTH_NM, -1.0, 1.0)
    theta = np.degrees(np.arccos(ratio))

    merged = {
        **cy3b_row.to_dict(),
        **atto_row.to_dict(),
        "dx (nm)": dx_raw,
        "dy (nm)": dy_raw,
        "Distance (nm)": distance,
        "Azimuthal Angle (deg)": azimuth,
        "Theta (deg)": theta
    }

    rows_out.append(merged)

output_df = pd.DataFrame(rows_out)

# --------------------------------------------------------------------------------------
# SAVE OUTPUT
# --------------------------------------------------------------------------------------
with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
    output_df.to_excel(writer, sheet_name="Paired_Results", index=False)

print(f"Saved: {OUTPUT_FILE}")
print(f"Pairs kept: {len(output_df)}")


# ======================================================================================
# SECTION 2 — THRESHOLDING BEFORE SCATTER PLOTS
# ======================================================================================

# --------------------------------------------------------------------------------------
# USER-EDITABLE THRESHOLDS
# Change these as needed
# Set to None if you do not want that threshold applied
# --------------------------------------------------------------------------------------

# Cy3b thresholds
CY3B_INTENSITY_MIN = 100
CY3B_INTENSITY_MAX = 2000
CY3B_UNCERTAINTY_MIN = 0
CY3B_UNCERTAINTY_MAX = 40

# ATTO647N thresholds
ATTO_INTENSITY_MIN = 100
ATTO_INTENSITY_MAX = 2000
ATTO_UNCERTAINTY_MIN = 0
ATTO_UNCERTAINTY_MAX = 40

# Coordinate thresholds
CY3B_X_MIN = None
CY3B_X_MAX = None
CY3B_Y_MIN = None
CY3B_Y_MAX = None

ATTO_X_MIN = None
ATTO_X_MAX = None
ATTO_Y_MIN = None
ATTO_Y_MAX = None

# --------------------------------------------------------------------------------------
# HELPER FUNCTION
# --------------------------------------------------------------------------------------
def in_range(series, min_val=None, max_val=None):
    mask = pd.Series(True, index=series.index)
    if min_val is not None:
        mask &= series >= min_val
    if max_val is not None:
        mask &= series <= max_val
    return mask

# --------------------------------------------------------------------------------------
# APPLY THRESHOLDS TO output_df DIRECTLY
# --------------------------------------------------------------------------------------
plot_df = output_df.copy()

mask = (
    in_range(plot_df["Cy3b_intensity [photon]"], CY3B_INTENSITY_MIN, CY3B_INTENSITY_MAX) &
    in_range(plot_df["Cy3b_uncertainty_xy [nm]"], CY3B_UNCERTAINTY_MIN, CY3B_UNCERTAINTY_MAX) &
    in_range(plot_df["ATTO647N_intensity [photon]"], ATTO_INTENSITY_MIN, ATTO_INTENSITY_MAX) &
    in_range(plot_df["ATTO647N_uncertainty_xy [nm]"], ATTO_UNCERTAINTY_MIN, ATTO_UNCERTAINTY_MAX) &
    in_range(plot_df["Cy3b_x [nm]"], CY3B_X_MIN, CY3B_X_MAX) &
    in_range(plot_df["Cy3b_y [nm]"], CY3B_Y_MIN, CY3B_Y_MAX) &
    in_range(plot_df["ATTO647N_x [nm]"], ATTO_X_MIN, ATTO_X_MAX) &
    in_range(plot_df["ATTO647N_y [nm]"], ATTO_Y_MIN, ATTO_Y_MAX)
)

plot_df = plot_df[mask].copy()

print(f"Pairs before thresholding: {len(output_df)}")
print(f"Pairs after thresholding:  {len(plot_df)}")
print(f"Pairs removed:             {len(output_df) - len(plot_df)}")


# ======================================================================================
# SECTION 3 — SCATTER PLOT + 10× ARROWS
# ======================================================================================

# --------------------------------------------------------------------------------------
# EXTRACT COORDINATES
# --------------------------------------------------------------------------------------
x_c1 = plot_df["Cy3b_x [nm]"].to_numpy()
y_c1 = plot_df["Cy3b_y [nm]"].to_numpy()

x_c2 = plot_df["ATTO647N_x [nm]"].to_numpy()
y_c2 = plot_df["ATTO647N_y [nm]"].to_numpy()

distances = plot_df["Distance (nm)"].to_numpy()

# --------------------------------------------------------------------------------------
# SCALE ARROWS (10× BIGGER)
# --------------------------------------------------------------------------------------
arrow_scale = 10.0

dx = (x_c2 - x_c1) * arrow_scale
dy = (y_c2 - y_c1) * arrow_scale

# --------------------------------------------------------------------------------------
# PLOT 1 — SCATTER + BLACK ARROWS
# --------------------------------------------------------------------------------------
plt.figure(figsize=(10, 8))

plt.scatter(
    x_c1, y_c1,
    color="green",
    alpha=0.2,
    s=20,
    label="C1 (TIRF 560)"
)

plt.scatter(
    x_c2, y_c2,
    color="red",
    alpha=0.2,
    s=20,
    label="C2 (TIRF 647N)"
)

plt.quiver(
    x_c1, y_c1,
    dx, dy,
    angles="xy",
    scale_units="xy",
    scale=1,
    color="black",
    width=0.003,
    headwidth=6,
    headlength=8,
    alpha= 1.0
)

plt.xlabel("X Position (nm)")
plt.ylabel("Y Position (nm)")
plt.title("Cy3b–ATTO647N Pairing with Azimuthal Direction (10× Arrows)")
plt.legend()
plt.grid(True)
plt.gca().invert_yaxis()
plt.tight_layout()
plt.show()


# ======================================================================================
# SECTION 4 — ARROW-ONLY PLOT WITH DISTANCE COLORBAR
# ======================================================================================

# --------------------------------------------------------------------------------------
# COLORMAP: SHORTER DISTANCE = GREENER, LONGER DISTANCE = REDDER
# --------------------------------------------------------------------------------------
cmap = plt.cm.get_cmap("RdYlGn_r")
norm = mcolors.Normalize(vmin=distances.min(), vmax=distances.max())

# --------------------------------------------------------------------------------------
# PLOT 2 — ARROWS ONLY, COLOR-CODED BY DISTANCE
# --------------------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 8))

q = ax.quiver(
    x_c1, y_c1,
    dx, dy,
    distances,
    cmap=cmap,
    norm=norm,
    angles="xy",
    scale_units="xy",
    scale=1,
    width=0.004,
    headwidth=6,
    headlength=8,
    headaxislength=7,
    alpha=0.95
)

# --------------------------------------------------------------------------------------
# COLORBAR
# --------------------------------------------------------------------------------------
cbar = plt.colorbar(q, ax=ax)
cbar.set_label("Distance (nm)")

# --------------------------------------------------------------------------------------
# LABELS
# --------------------------------------------------------------------------------------
ax.set_xlabel("X Position (nm)")
ax.set_ylabel("Y Position (nm)")
ax.set_title("Cy3b–ATTO647N Direction Arrows Only (Color-Coded by Distance)")
ax.grid(True)
ax.invert_yaxis()

plt.tight_layout()
plt.show()
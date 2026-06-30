from __future__ import annotations

import numpy as np
import pandas as pd

BANDS = ["u", "g", "r", "i", "z"]
COLOR_PAIRS = [
    ("u", "g"), ("g", "r"), ("r", "i"), ("i", "z"),
    ("u", "r"), ("u", "i"), ("u", "z"), ("g", "i"), ("g", "z"), ("r", "z"),
]
CURVATURE_SPECS = [("u", "g", "r"), ("g", "r", "i"), ("r", "i", "z"), ("u", "r", "z")]


def _safe_divide(a, b, eps=1e-6):
    return a / (np.abs(b) + eps)


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()

    # Cast bands to float32
    for col in BANDS + ["alpha", "delta", "redshift"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce").astype("float32")

    # --- Color indices (magnitude differences and ratios) ---
    for a, b in COLOR_PAIRS:
        if a in out.columns and b in out.columns:
            color = out[a] - out[b]
            out[f"{a}_minus_{b}"] = color
            out[f"{a}_div_{b}"] = _safe_divide(out[a], out[b])
            out[f"flux_ratio_{a}_{b}"] = np.power(10.0, -0.4 * color.clip(-50, 50)).astype("float32")

    # --- Magnitude summary stats ---
    mag = out[BANDS]
    out["mag_mean"] = mag.mean(axis=1)
    out["mag_std"] = mag.std(axis=1)
    out["mag_min"] = mag.min(axis=1)
    out["mag_max"] = mag.max(axis=1)
    out["mag_range"] = out["mag_max"] - out["mag_min"]
    out["blue_mean"] = out[["u", "g"]].mean(axis=1)
    out["red_mean"] = out[["i", "z"]].mean(axis=1)
    out["blue_minus_red"] = out["blue_mean"] - out["red_mean"]
    out["spectral_slope_ugriz"] = (out["z"] - out["u"]) / 4.0

    # --- Flux (linear scale from magnitudes) ---
    for b in BANDS:
        out[f"flux_{b}"] = np.power(10.0, -0.4 * out[b].clip(-50, 50)).astype("float32")
    flux_cols = [f"flux_{b}" for b in BANDS]
    out["flux_mean"] = out[flux_cols].mean(axis=1)
    out["flux_std"] = out[flux_cols].std(axis=1)
    out["flux_range"] = out[flux_cols].max(axis=1) - out[flux_cols].min(axis=1)

    # --- Flux share and entropy ---
    flux_values = out[flux_cols].clip(lower=0).astype("float64")
    flux_sum = flux_values.sum(axis=1).replace(0, np.nan)
    share_cols = []
    for b in BANDS:
        sc = f"flux_share_{b}"
        out[sc] = (out[f"flux_{b}"] / flux_sum).fillna(0).astype("float32")
        share_cols.append(sc)
    share = out[share_cols].clip(lower=1e-12)
    out["flux_entropy"] = (-share.mul(np.log(share), axis=0).sum(axis=1)).astype("float32")
    out["flux_share_max"] = out[share_cols].max(axis=1).astype("float32")
    out["flux_share_min"] = out[share_cols].min(axis=1).astype("float32")
    out["brightest_band_idx"] = flux_values.to_numpy().argmax(axis=1).astype("int8")
    out["faintest_band_idx"] = flux_values.to_numpy().argmin(axis=1).astype("int8")

    # --- Color curvature (second differences — concavity of SED) ---
    for a, b, c in CURVATURE_SPECS:
        if {a, b, c}.issubset(out.columns):
            out[f"curvature_{a}_{b}_{c}"] = (out[a] - 2.0 * out[b] + out[c]).astype("float32")

    # --- Redshift features ---
    red = out["redshift"].astype("float32")
    out["redshift_abs"] = red.abs()
    out["redshift_sq"] = red ** 2
    out["redshift_log1p"] = np.log1p(red.clip(lower=0))
    out["redshift_signed_log1p"] = np.sign(red) * np.log1p(red.abs())
    out["redshift_neg_flag"] = (red < 0).astype("int8")
    out["near_zero_redshift"] = (red.abs() < 0.1).astype("int8")
    out["high_redshift"] = (red > 1.0).astype("int8")
    out["very_high_redshift"] = (red > 2.0).astype("int8")
    out["redshift_tiny_abs"] = (red.abs() < 0.02).astype("int8")
    out["redshift_low"] = ((red >= 0.02) & (red < 0.15)).astype("int8")
    out["redshift_mid"] = ((red >= 0.15) & (red < 0.8)).astype("int8")
    out["redshift_qso_mid"] = ((red >= 0.8) & (red < 1.6)).astype("int8")
    out["redshift_qso_high"] = (red >= 1.6).astype("int8")
    out["redshift_clip_0_4"] = red.clip(0, 4).astype("float32")

    # Redshift × color interactions
    interact_cols = ["mag_mean", "blue_minus_red", "u_minus_g", "g_minus_r", "i_minus_z",
                     "curvature_u_g_r", "curvature_g_r_i", "curvature_r_i_z"]
    for col in interact_cols:
        if col in out.columns:
            out[f"redshift_x_{col}"] = (red * out[col]).astype("float32")

    # --- Categorical encodings ---
    spectral_map = {"O/B": 0, "A/F": 1, "G/K": 2, "M": 3, "unknown": -1}
    out["spectral_type_enc"] = out["spectral_type"].map(spectral_map).fillna(-1).astype("int8")
    out["galaxy_pop_enc"] = (out["galaxy_population"] == "Red_Sequence").astype("int8")

    out = out.drop(columns=["spectral_type", "galaxy_population"])
    return out

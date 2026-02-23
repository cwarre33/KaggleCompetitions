"""Feature engineering and preprocessing."""
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add interaction features."""
    df = df.copy()
    if "Max HR" in df.columns and "Age" in df.columns:
        df["MaxHR_per_Age"] = df["Max HR"] / (df["Age"] + 1)
    if "Cholesterol" in df.columns and "BP" in df.columns:
        df["Chol_BP"] = df["Cholesterol"] * df["BP"]
    return df


def preprocess(df: pd.DataFrame, encoders: dict | None = None, fit: bool = True) -> tuple[np.ndarray, dict]:
    """
    Minimal preprocessing: fill missing, encode categoricals.
    Returns (X_array, encoders_dict).
    """
    df = df.copy()
    encoders = encoders or {}

    # Fill missing
    df = df.fillna(df.median(numeric_only=True))
    for c in df.select_dtypes(include=["object"]).columns:
        df[c] = df[c].fillna(df[c].mode().iloc[0] if len(df) > 0 else "")

    # Encode object columns
    for col in df.select_dtypes(include=["object"]).columns:
        if fit:
            enc = LabelEncoder()
            df[col] = enc.fit_transform(df[col].astype(str))
            encoders[col] = enc
        elif col in encoders:
            df[col] = encoders[col].transform(df[col].astype(str))

    X = df.select_dtypes(include=[np.number]).values
    return X, encoders

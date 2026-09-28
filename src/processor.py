import re
import numpy as np
import pandas as pd

COUNTRY_PATTERN = re.compile(r",\s*([A-Za-z][A-Za-z .'-]{1,60})\s*$")


def extract_country(place):
    if not isinstance(place, str) or not place.strip():
        return "Unknown"

    match = COUNTRY_PATTERN.search(place.strip())
    if match:
        return match.group(1).strip()

    match = re.search(r"\bof\s+(.+)$", place, flags=re.I)
    if match:
        candidate = match.group(1).strip()
        if "," in candidate:
            candidate = candidate.split(",")[-1].strip()
        return candidate[:80]

    return "Unknown"


def depth_category(depth):
    if pd.isna(depth):
        return "Unknown"
    if depth < 50:
        return "Shallow"
    if depth < 100:
        return "Moderate"
    if depth <= 300:
        return "Intermediate"
    return "Deep"


def magnitude_category(mag):
    if pd.isna(mag):
        return "Unknown"
    if mag >= 7:
        return "Major (7+)"
    if mag >= 6:
        return "Strong (6–6.9)"
    if mag >= 5:
        return "Moderate (5–5.9)"
    if mag >= 4:
        return "Light (4–4.9)"
    return "Minor (<4)"


def clean_text(value):
    return None if pd.isna(value) else str(value).strip()


def process_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    for col in ("time", "updated"):
        df[col] = pd.to_datetime(df[col], unit="ms", errors="coerce", utc=True)

    numeric_cols = [
        "latitude", "longitude", "depth_km", "mag", "tsunami", "sig",
        "nst", "dmin", "rms", "gap", "magError", "depthError", "magNst"
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    text_cols = [
        "id", "magType", "place", "status", "net", "locationSource",
        "magSource", "types", "ids", "sources", "type"
    ]
    for col in text_cols:
        df[col] = df[col].map(clean_text)

    df["tsunami"] = df["tsunami"].fillna(0).astype(int)
    df["sig"] = df["sig"].fillna(0)

    for col in ["mag", "depth_km", "nst", "dmin", "rms", "gap", "magError", "depthError", "magNst"]:
        if df[col].notna().any():
            df[col] = df[col].fillna(df[col].median())

    df["status"] = df["status"].fillna("unknown").str.lower()
    df["magType"] = df["magType"].fillna("unknown")
    df["type"] = df["type"].fillna("unknown")

    df["country"] = df["place"].map(extract_country)

    df["year"] = df["time"].dt.year
    df["month"] = df["time"].dt.month
    df["month_name"] = df["time"].dt.month_name()
    df["day"] = df["time"].dt.day
    df["day_of_week"] = df["time"].dt.day_name()
    df["hour"] = df["time"].dt.hour

    df["depth_category"] = df["depth_km"].map(depth_category)
    df["magnitude_category"] = df["mag"].map(magnitude_category)
    df["shallow_flag"] = (df["depth_km"] < 50).astype(int)
    df["deep_focus_flag"] = (df["depth_km"] > 300).astype(int)
    df["strong_flag"] = (df["mag"] >= 6).astype(int)
    df["major_flag"] = (df["mag"] >= 7).astype(int)

    gap_score = np.clip(1 - (df["gap"].fillna(360) / 360), 0, 1)
    rms_score = np.clip(1 - (df["rms"].fillna(5) / 5), 0, 1)
    station_score = np.clip(df["nst"].fillna(0) / 100, 0, 1)
    df["quality_score"] = ((gap_score + rms_score + station_score) / 3 * 100).round(1)

    df.loc[~df["latitude"].between(-90, 90), "latitude"] = np.nan
    df.loc[~df["longitude"].between(-180, 180), "longitude"] = np.nan

    df = df.drop_duplicates(subset=["id"], keep="last")
    return df.sort_values("time").reset_index(drop=True)


def save_processed(df: pd.DataFrame, path):
    out = df.copy()
    for col in ["time", "updated"]:
        if col in out:
            out[col] = out[col].astype(str)
    out.to_csv(path, index=False)

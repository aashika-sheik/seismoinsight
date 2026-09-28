import calendar
import json
import time as time_module
from datetime import datetime, timezone
from typing import List, Dict

import requests
import pandas as pd

from config import USGS_URL, RAW_JSON_PATH


def month_ranges(start_year: int, end_year: int):
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            start = datetime(year, month, 1, tzinfo=timezone.utc)
            last_day = calendar.monthrange(year, month)[1]
            end = datetime(year, month, last_day, 23, 59, 59, tzinfo=timezone.utc)
            yield start, end


def fetch_month(start: datetime, end: datetime, min_magnitude: float = 2.5) -> List[Dict]:
    params = {
        "format": "geojson",
        "starttime": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "endtime": end.strftime("%Y-%m-%dT%H:%M:%S"),
        "minmagnitude": min_magnitude,
        "orderby": "time-asc",
        "limit": 20000,
    }
    response = requests.get(USGS_URL, params=params, timeout=60)
    response.raise_for_status()
    return response.json().get("features", [])


def fetch_last_n_years(years: int = 5, min_magnitude: float = 2.5, sleep_seconds: float = 0.15):
    now = datetime.now(timezone.utc)
    end_year = now.year
    start_year = end_year - years + 1
    all_events = []

    for start, end in month_ranges(start_year, end_year):
        if start > now:
            continue
        end = min(end, now)
        try:
            events = fetch_month(start, end, min_magnitude)
            all_events.extend(events)
            print(f"{start:%Y-%m}: {len(events)} events")
        except requests.RequestException as exc:
            print(f"Failed {start:%Y-%m}: {exc}")
        time_module.sleep(sleep_seconds)

    RAW_JSON_PATH.write_text(json.dumps(all_events, ensure_ascii=False), encoding="utf-8")
    return all_events


def raw_json_to_dataframe(features: list) -> pd.DataFrame:
    rows = []
    for feature in features:
        props = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coords = geometry.get("coordinates") or [None, None, None]

        rows.append({
            "id": feature.get("id"),
            "time": props.get("time"),
            "updated": props.get("updated"),
            "latitude": coords[1] if len(coords) > 1 else None,
            "longitude": coords[0] if len(coords) > 0 else None,
            "depth_km": coords[2] if len(coords) > 2 else None,
            "mag": props.get("mag"),
            "magType": props.get("magType"),
            "place": props.get("place"),
            "status": props.get("status"),
            "tsunami": props.get("tsunami"),
            "sig": props.get("sig"),
            "net": props.get("net"),
            "nst": props.get("nst"),
            "dmin": props.get("dmin"),
            "rms": props.get("rms"),
            "gap": props.get("gap"),
            "magError": props.get("magError"),
            "depthError": props.get("depthError"),
            "magNst": props.get("magNst"),
            "locationSource": props.get("locationSource"),
            "magSource": props.get("magSource"),
            "types": props.get("types"),
            "ids": props.get("ids"),
            "sources": props.get("sources"),
            "type": props.get("type"),
        })
    return pd.DataFrame(rows)

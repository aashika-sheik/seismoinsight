import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from config import CSV_PATH
from src.database import create_database, get_engine, upsert_dataframe

if __name__ == "__main__":
    if not CSV_PATH.exists():
        raise FileNotFoundError("Run scripts/fetch_data.py first.")
    df = pd.read_csv(CSV_PATH)
    create_database()
    upsert_dataframe(get_engine(), df)
    print(f"Loaded {len(df):,} rows into MySQL.")

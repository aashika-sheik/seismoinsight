import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
from src.fetcher import fetch_last_n_years, raw_json_to_dataframe
from src.processor import process_dataframe, save_processed
from config import CSV_PATH

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--years", type=int, default=5)
    parser.add_argument("--min-magnitude", type=float, default=2.5)
    args = parser.parse_args()

    features = fetch_last_n_years(args.years, args.min_magnitude)
    raw_df = raw_json_to_dataframe(features)
    clean_df = process_dataframe(raw_df)
    save_processed(clean_df, CSV_PATH)

    print(f"Raw records: {len(raw_df):,}")
    print(f"Clean records: {len(clean_df):,}")
    print(f"Saved: {CSV_PATH}")

if __name__ == "__main__":
    main()

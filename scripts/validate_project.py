from src.database import get_engine, read_sql, table_count

REQUIRED = {
    "id","time","updated","latitude","longitude","depth_km","mag","magType",
    "place","status","tsunami","sig","net","nst","dmin","rms","gap",
    "magError","depthError","magNst","locationSource","magSource","types",
    "ids","sources","type","country","year","month","month_name","day",
    "day_of_week","hour","depth_category","magnitude_category","shallow_flag",
    "deep_focus_flag","strong_flag","major_flag","quality_score"
}

def main():
    print("=== SeismoInsight validation ===")
    engine = get_engine()

    version = read_sql(engine, "SELECT VERSION() AS version").iloc[0]["version"]
    print("MySQL:", version)

    count = table_count(engine)
    print("Rows:", f"{count:,}")
    assert count > 0, "earthquakes table is empty"

    cols = set(read_sql(engine, "SHOW COLUMNS FROM earthquakes")["Field"])
    missing = REQUIRED - cols
    print("Columns:", len(cols))
    print("Missing required columns:", sorted(missing))
    assert not missing, f"Missing columns: {sorted(missing)}"

    dup = int(read_sql(engine, """
        SELECT COUNT(*) - COUNT(DISTINCT id) AS duplicate_ids
        FROM earthquakes
    """).iloc[0]["duplicate_ids"])
    print("Duplicate IDs:", dup)
    assert dup == 0, "Duplicate IDs found"

    stats = read_sql(engine, """
        SELECT
          MIN(time) AS first_event,
          MAX(time) AS latest_event,
          MIN(mag) AS min_mag,
          MAX(mag) AS max_mag,
          MIN(depth_km) AS min_depth,
          MAX(depth_km) AS max_depth
        FROM earthquakes
    """).iloc[0]
    print("Date range:", stats["first_event"], "to", stats["latest_event"])
    print("Magnitude range:", stats["min_mag"], "to", stats["max_mag"])
    print("Depth range:", stats["min_depth"], "to", stats["max_depth"])

    assert 0 <= float(stats["max_mag"]) <= 10
    assert float(stats["min_mag"]) >= -10

    derived = read_sql(engine, """
        SELECT
          COUNT(*) AS total,
          SUM(year IS NULL) AS missing_year,
          SUM(depth_category IS NULL) AS missing_depth_category,
          SUM(magnitude_category IS NULL) AS missing_magnitude_category
        FROM earthquakes
    """).iloc[0]
    print("Derived-field null checks:", dict(derived))
    assert int(derived["missing_year"]) == 0
    assert int(derived["missing_depth_category"]) == 0
    assert int(derived["missing_magnitude_category"]) == 0

    strongest = read_sql(engine, """
        SELECT id, mag FROM earthquakes ORDER BY mag DESC LIMIT 1
    """)
    print("Strongest event:", strongest.to_dict("records")[0])

    yearly = read_sql(engine, """
        SELECT year, COUNT(*) AS events
        FROM earthquakes GROUP BY year ORDER BY year
    """)
    print("Year buckets:", len(yearly))

    print("\nVALIDATION: PASS")

if __name__ == "__main__":
    main()

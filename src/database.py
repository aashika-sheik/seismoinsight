from urllib.parse import quote_plus
import pandas as pd
from sqlalchemy import create_engine, text
from config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE


def mysql_url(database=None):
    database = database or MYSQL_DATABASE
    password = quote_plus(MYSQL_PASSWORD)
    return f"mysql+pymysql://{MYSQL_USER}:{password}@{MYSQL_HOST}:{MYSQL_PORT}/{database}"


def create_database():
    engine = create_engine(mysql_url("mysql"), pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}`"))
        conn.commit()


def get_engine():
    return create_engine(mysql_url(), pool_pre_ping=True, pool_recycle=3600, future=True)


def initialize_table(engine):
    ddl = """
    CREATE TABLE IF NOT EXISTS earthquakes (
        id VARCHAR(64) PRIMARY KEY,
        time DATETIME NULL,
        updated DATETIME NULL,
        latitude DOUBLE NULL,
        longitude DOUBLE NULL,
        depth_km DOUBLE NULL,
        mag DOUBLE NULL,
        magType VARCHAR(30) NULL,
        place VARCHAR(500) NULL,
        status VARCHAR(40) NULL,
        tsunami INT NULL,
        sig INT NULL,
        net VARCHAR(30) NULL,
        nst DOUBLE NULL,
        dmin DOUBLE NULL,
        rms DOUBLE NULL,
        gap DOUBLE NULL,
        magError DOUBLE NULL,
        depthError DOUBLE NULL,
        magNst DOUBLE NULL,
        locationSource VARCHAR(50) NULL,
        magSource VARCHAR(50) NULL,
        types TEXT NULL,
        ids TEXT NULL,
        sources TEXT NULL,
        type VARCHAR(50) NULL,
        country VARCHAR(120) NULL,
        year INT NULL,
        month INT NULL,
        month_name VARCHAR(20) NULL,
        day INT NULL,
        day_of_week VARCHAR(20) NULL,
        hour INT NULL,
        depth_category VARCHAR(30) NULL,
        magnitude_category VARCHAR(30) NULL,
        shallow_flag INT NULL,
        deep_focus_flag INT NULL,
        strong_flag INT NULL,
        major_flag INT NULL,
        quality_score DOUBLE NULL,
        INDEX idx_time (time),
        INDEX idx_mag (mag),
        INDEX idx_country (country),
        INDEX idx_depth (depth_km)
    )
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))


def upsert_dataframe(engine, df):
    initialize_table(engine)
    columns = list(df.columns)
    placeholders = ", ".join([f":{c}" for c in columns])
    updates = ", ".join([f"{c}=VALUES({c})" for c in columns if c != "id"])
    sql = text(
        f"INSERT INTO earthquakes ({', '.join(columns)}) VALUES ({placeholders}) "
        f"ON DUPLICATE KEY UPDATE {updates}"
    )

    clean = df.copy()
    for col in ["time", "updated"]:
        clean[col] = pd.to_datetime(clean[col], errors="coerce").dt.tz_localize(None)

    clean = clean.where(pd.notna(clean), None)

    records = clean.astype(object).where(pd.notna(clean), None).to_dict(orient="records")

    with engine.begin() as conn:
        for i in range(0, len(records), 1000):
            conn.execute(sql, records[i:i + 1000])


def read_sql(engine, query, params=None):
    return pd.read_sql(text(query), engine, params=params or {})


def table_count(engine):
    try:
        return int(read_sql(engine, "SELECT COUNT(*) AS n FROM earthquakes").iloc[0]["n"])
    except Exception:
        return 0

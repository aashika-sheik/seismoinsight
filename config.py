from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
EXPORT_DIR = DATA_DIR / "exports"

for directory in (DATA_DIR, RAW_DIR, PROCESSED_DIR, EXPORT_DIR):
    directory.mkdir(parents=True, exist_ok=True)

USGS_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "seismoinsight")
USE_MYSQL = os.getenv("USE_MYSQL", "true").lower() == "true"

CSV_PATH = PROCESSED_DIR / "earthquakes.csv"
RAW_JSON_PATH = RAW_DIR / "earthquakes_raw.json"

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.database import create_database, get_engine, initialize_table

if __name__ == "__main__":
    create_database()
    initialize_table(get_engine())
    print("SeismoInsight MySQL database/table initialized.")

# SeismoInsight
## Global Seismic Intelligence & Earthquake Analytics Platform

SeismoInsight turns USGS earthquake event data into an interactive analytics product.

### Stack
Python, Requests, Pandas, Regex, MySQL + SQLAlchemy, Plotly, Streamlit.

### Pipeline
USGS API -> Raw JSON -> Pandas/Regex cleaning -> Feature engineering -> MySQL -> SQL analytics -> Streamlit

### Pages
1. Dashboard
2. Global Map
3. Trends & Analysis
4. Seismic Activity Zones
5. Earthquake Explorer
6. Regional Comparison
7. Data Quality
8. Reports

### Setup
```bash
python -m venv .venv
```

Windows:
```powershell
.venv\Scripts\activate
```

Install:
```bash
pip install -r requirements.txt
```

Create MySQL database:
```sql
CREATE DATABASE seismoinsight;
```

Copy `.env.example` to `.env` and set credentials.

Initialize:
```bash
python scripts/init_db.py
```

Fetch latest five years:
```bash
python scripts/fetch_data.py --years 5 --min-magnitude 2.5
```

Load MySQL:
```bash
python scripts/load_mysql.py
```

Run:
```bash
streamlit run app.py
```

### No MySQL
Set `USE_MYSQL=false` in `.env`, then generate/fetch CSV data. The dashboard falls back to `data/processed/earthquakes.csv`.

### Important
This is an analytics application, not an earthquake prediction or emergency-warning system.
Seismic Activity Zones are historical observed-activity classifications, not official hazard maps.
Casualties and economic loss are not fabricated because they are not included in the supplied 26-feature dataset.

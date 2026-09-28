# SeismoInsight — Global Seismic Trends

An end-to-end earthquake analytics project built from the **USGS Earthquake API**, Python/Pandas/Regex, MySQL and Streamlit.

## 1. Problem statement

Analyze global earthquake data to identify seismic patterns, trends, depth patterns and observed activity regions using API retrieval, preprocessing and SQL analytics.

**Important:** SeismoInsight is an analytics application. It is **not** an earthquake prediction or emergency-warning system.

## 2. Technology stack

- Python
- Requests
- Pandas / NumPy
- Regular Expressions (Regex)
- MySQL 8.0
- SQLAlchemy + PyMySQL
- Plotly
- Streamlit

## 3. Architecture

```text
USGS Earthquake API
        ↓
Monthly API retrieval
        ↓
Raw JSON
        ↓
Pandas + Regex cleaning
        ↓
Feature engineering
        ↓
Processed CSV
        ↓
MySQL earthquakes table
        ↓
SQL analytical queries
        ↓
Python analytics
        ↓
Streamlit dashboard
```

## 4. Dataset

The project retrieves the last five years of USGS earthquake events with a minimum magnitude of 2.5.

The current project dataset contains **130,160 real USGS event records** loaded into MySQL.

The supplied project brief defines 26 source features:
`id, time, updated, latitude, longitude, depth_km, mag, magType, place, status, tsunami, sig, net, nst, dmin, rms, gap, magError, depthError, magNst, locationSource, magSource, types, ids, sources, type`.

Derived fields include:
`country, year, month, month_name, day, day_of_week, hour, depth_category, magnitude_category, shallow_flag, deep_focus_flag, strong_flag, major_flag, quality_score`.

`quality_score` is a **project-defined analytical index** calculated from gap, RMS and station coverage. It is not an official USGS quality rating.

## 5. Data preparation

The Python pipeline:

1. Retrieves monthly GeoJSON responses from USGS.
2. Extracts properties and geometry fields.
3. Converts millisecond timestamps to UTC datetimes.
4. Converts numeric fields using Pandas.
5. Cleans text fields.
6. Uses Regex to derive the `country` field from the USGS `place` string.
7. Creates year/month/day/day-of-week/hour fields.
8. Creates shallow/deep and magnitude-category flags.
9. Removes duplicate event IDs.
10. Saves the processed dataset.
11. Loads the cleaned records into MySQL.

Missing optional USGS measurements remain missing/NULL when the source does not provide them; they are not fabricated.

## 6. MySQL

Database:

```sql
CREATE DATABASE seismoinsight;
USE seismoinsight;
```

Table:

```text
earthquakes
```

The table contains the 26 supplied source features plus the project-derived analytical fields.

Verify:

```sql
SELECT COUNT(*) AS total_events FROM earthquakes;
```

Expected current count:

```text
130160
```

## 7. SQL analysis

`sql/analysis_queries.sql` contains the project analytical query pack for the 30 tasks in the brief.

Covered tasks include:

- strongest and deepest earthquakes
- shallow + strong earthquakes
- magnitude type comparison
- yearly/monthly/day/hour patterns
- reporting networks
- reviewed vs automatic records
- event types and associated data types
- station coverage
- tsunami trends
- country average magnitude
- same-month shallow/deep activity
- year-over-year growth
- combined frequency/magnitude activity index
- equator ±5° analysis
- shallow/deep ratio
- tsunami vs non-tsunami magnitude difference
- lowest measurement reliability
- consecutive events within 50 km and one hour using a Haversine calculation
- deep-focus regions

### Dataset limitations

Tasks requiring **casualties, economic loss or alert level** cannot be calculated from the supplied 26-feature schema because those fields are absent.

The project deliberately does **not fabricate** those values. They are marked as unavailable in the SQL and dashboard.

Likewise, the supplied schema does not contain a canonical `continent` field. Country-level analysis is therefore used where appropriate, and geographic latitude/longitude logic is used for the equator analysis.

## 8. Streamlit dashboard

Run:

```powershell
streamlit run app.py
```

Dashboard pages:

1. Dashboard
2. Global Map
3. Trends & Analysis
4. Seismic Activity Zones
5. Earthquake Explorer
6. Regional Comparison
7. SQL Analysis
8. Data Quality
9. Reports

The dashboard prefers MySQL when `USE_MYSQL=true` and a populated `earthquakes` table is available. It falls back to the processed CSV if MySQL is unavailable.

### Seismic Activity Zones

These are **historical observed-activity classifications** based on event frequency and average magnitude. They are not official seismic hazard maps and do not predict future earthquakes.

## 9. Setup on Windows / VS Code

From the project folder:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure `.env`:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=YOUR_PASSWORD
MYSQL_DATABASE=seismoinsight
USE_MYSQL=true
```

Initialize the table if needed:

```powershell
python scripts\init_db.py
```

Fetch data only when a fresh dataset is required:

```powershell
python scripts\fetch_data.py --years 5 --min-magnitude 2.5
```

Load into MySQL:

```powershell
python scripts\load_mysql.py
```

Run dashboard:

```powershell
python -m streamlit run app.py
```

## 10. Validation

Run:

```powershell
python scripts\validate_project.py
```

The validator checks:

- MySQL connection
- database/table availability
- row count
- duplicate IDs
- date range
- magnitude/depth ranges
- required columns
- missingness in source fields
- derived fields
- basic SQL smoke tests

## 11. Project evaluation alignment

| Evaluation area | Implementation |
|---|---|
| Data Cleaning Accuracy | Pandas, Regex, datetime conversion, numeric/text cleaning, duplicate handling |
| SQL Query Effectiveness | 30-task SQL analysis pack, CTEs, window functions and Haversine analysis |
| Visualization & Dashboard | Streamlit + Plotly + filters + maps + analysis pages |
| Documentation | README, methodology, limitations and interpretation notes |
| Organization | Separate fetch, processing, database, analytics, SQL and dashboard modules |

## 12. Responsible interpretation

The dashboard describes **observed historical records** in the selected dataset. High historical event activity should not be interpreted as a prediction of a future earthquake.

The project is intended for learning, exploratory analytics and demonstration of an end-to-end data workflow.

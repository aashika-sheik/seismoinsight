-- SeismoInsight: SQL Analysis Pack
-- MySQL 8.0+
-- Source table: earthquakes
--
-- Tasks 11-13 and 20 require casualties, economic_loss and alert fields.
-- Those fields are NOT present in the supplied 26-feature USGS schema.
-- They are intentionally not fabricated. See README for the limitation.
--
-- "country" is derived from the USGS place string. The supplied schema does
-- not contain a canonical continent field, so continent-style tasks use
-- latitude/longitude geographic bands only where explicitly noted.

USE seismoinsight;

-- ============================================================
-- 1. Top 10 strongest earthquakes
-- ============================================================
SELECT id, time, place, mag, depth_km, tsunami
FROM earthquakes
ORDER BY mag DESC, time ASC
LIMIT 10;

-- ============================================================
-- 2. Top 10 deepest earthquakes
-- ============================================================
SELECT id, time, place, mag, depth_km
FROM earthquakes
ORDER BY depth_km DESC
LIMIT 10;

-- ============================================================
-- 3. Shallow earthquakes (<50 km) with magnitude > 7.5
-- ============================================================
SELECT id, time, place, mag, depth_km
FROM earthquakes
WHERE depth_km < 50 AND mag > 7.5
ORDER BY mag DESC;

-- ============================================================
-- 4. Average depth by geographic region proxy
-- The original schema has no continent column; country is the
-- available geographic dimension.
-- ============================================================
SELECT country, COUNT(*) AS events,
       ROUND(AVG(depth_km), 2) AS avg_depth_km
FROM earthquakes
WHERE country IS NOT NULL AND country <> 'Unknown'
GROUP BY country
ORDER BY avg_depth_km DESC;

-- ============================================================
-- 5. Average magnitude by magnitude type
-- ============================================================
SELECT magType, COUNT(*) AS events,
       ROUND(AVG(mag), 3) AS avg_magnitude
FROM earthquakes
GROUP BY magType
ORDER BY events DESC;

-- ============================================================
-- 6. Year with the most earthquakes
-- ============================================================
SELECT year, COUNT(*) AS events
FROM earthquakes
GROUP BY year
ORDER BY events DESC
LIMIT 1;

-- ============================================================
-- 7. Month with the highest number of earthquakes
-- ============================================================
SELECT month, month_name, COUNT(*) AS events
FROM earthquakes
GROUP BY month, month_name
ORDER BY events DESC
LIMIT 1;

-- ============================================================
-- 8. Day of week with the most earthquakes
-- ============================================================
SELECT day_of_week, COUNT(*) AS events
FROM earthquakes
GROUP BY day_of_week
ORDER BY events DESC
LIMIT 1;

-- ============================================================
-- 9. Earthquakes by hour of day
-- ============================================================
SELECT hour, COUNT(*) AS events
FROM earthquakes
GROUP BY hour
ORDER BY hour;

-- ============================================================
-- 10. Most active reporting networks
-- ============================================================
SELECT net, COUNT(*) AS events
FROM earthquakes
WHERE net IS NOT NULL
GROUP BY net
ORDER BY events DESC
LIMIT 10;

-- ============================================================
-- 11. Top 5 places by casualties
-- NOT AVAILABLE: casualties is not in the supplied schema.
-- ============================================================

-- ============================================================
-- 12. Economic loss by continent
-- NOT AVAILABLE: economic_loss and continent are not in schema.
-- ============================================================

-- ============================================================
-- 13. Average economic loss by alert level
-- NOT AVAILABLE: economic_loss and alert are not in schema.
-- ============================================================

-- ============================================================
-- 14. Reviewed vs automatic earthquakes
-- ============================================================
SELECT status, COUNT(*) AS events
FROM earthquakes
GROUP BY status
ORDER BY events DESC;

-- ============================================================
-- 15. Count by earthquake/event type
-- ============================================================
SELECT type, COUNT(*) AS events
FROM earthquakes
GROUP BY type
ORDER BY events DESC;

-- ============================================================
-- 16. Count by associated data types
-- ============================================================
SELECT
    CASE
        WHEN types LIKE '%shakemap%' THEN 'shakemap'
        WHEN types LIKE '%dyfi%' THEN 'dyfi'
        WHEN types LIKE '%phase-data%' THEN 'phase-data'
        WHEN types LIKE '%origin%' THEN 'origin'
        ELSE 'other'
    END AS data_type,
    COUNT(*) AS events
FROM earthquakes
GROUP BY data_type
ORDER BY events DESC;

-- ============================================================
-- 17. Average RMS and gap by country
-- Continent is unavailable in the supplied 26 features.
-- ============================================================
SELECT country,
       COUNT(*) AS events,
       ROUND(AVG(rms), 3) AS avg_rms,
       ROUND(AVG(gap), 2) AS avg_gap
FROM earthquakes
WHERE country IS NOT NULL AND country <> 'Unknown'
GROUP BY country
ORDER BY avg_rms DESC, avg_gap DESC;

-- ============================================================
-- 18. Events with high station coverage
-- Threshold chosen explicitly as nst > 20.
-- ============================================================
SELECT id, time, place, mag, nst, gap, rms, quality_score
FROM earthquakes
WHERE nst > 20
ORDER BY nst DESC
LIMIT 100;

-- ============================================================
-- 19. Tsunami-flagged earthquakes per year
-- ============================================================
SELECT year, SUM(tsunami) AS tsunami_events
FROM earthquakes
GROUP BY year
ORDER BY year;

-- ============================================================
-- 20. Count by alert level
-- NOT AVAILABLE: alert is not in the supplied schema.
-- ============================================================

-- ============================================================
-- 21. Top 5 countries by average magnitude
-- Minimum 10 events avoids tiny-sample distortion.
-- ============================================================
SELECT country, COUNT(*) AS events,
       ROUND(AVG(mag), 3) AS avg_magnitude
FROM earthquakes
WHERE country IS NOT NULL AND country <> 'Unknown'
GROUP BY country
HAVING COUNT(*) >= 10
ORDER BY avg_magnitude DESC, events DESC
LIMIT 5;

-- ============================================================
-- 22. Countries with both shallow and deep-focus earthquakes
-- within the same month
-- ============================================================
SELECT country, year, month, month_name,
       SUM(shallow_flag) AS shallow_events,
       SUM(deep_focus_flag) AS deep_events
FROM earthquakes
WHERE country IS NOT NULL AND country <> 'Unknown'
GROUP BY country, year, month, month_name
HAVING SUM(shallow_flag) > 0 AND SUM(deep_focus_flag) > 0
ORDER BY country, year, month;

-- ============================================================
-- 23. Global year-over-year growth
-- ============================================================
WITH yearly AS (
    SELECT year, COUNT(*) AS events
    FROM earthquakes
    GROUP BY year
),
growth AS (
    SELECT year, events,
           LAG(events) OVER (ORDER BY year) AS previous_events
    FROM yearly
)
SELECT year, events, previous_events,
       ROUND((events - previous_events) /
             NULLIF(previous_events, 0) * 100, 2) AS yoy_growth_pct
FROM growth
ORDER BY year;

-- ============================================================
-- 24. Three most active regions using frequency + average magnitude
-- Transparent 65% frequency + 35% magnitude composite.
-- ============================================================
WITH region AS (
    SELECT country,
           COUNT(*) AS events,
           AVG(mag) AS avg_magnitude
    FROM earthquakes
    WHERE country IS NOT NULL AND country <> 'Unknown'
    GROUP BY country
    HAVING COUNT(*) >= 10
),
ranked AS (
    SELECT *,
           PERCENT_RANK() OVER (ORDER BY events) AS frequency_score,
           PERCENT_RANK() OVER (ORDER BY avg_magnitude) AS magnitude_score
    FROM region
)
SELECT country, events, ROUND(avg_magnitude, 3) AS avg_magnitude,
       ROUND(0.65 * frequency_score + 0.35 * magnitude_score, 4) AS activity_index
FROM ranked
ORDER BY activity_index DESC
LIMIT 3;

-- ============================================================
-- 25. Average earthquake depth within ±5° latitude of equator
-- ============================================================
SELECT country, COUNT(*) AS events,
       ROUND(AVG(depth_km), 2) AS avg_depth_km
FROM earthquakes
WHERE latitude BETWEEN -5 AND 5
  AND country IS NOT NULL AND country <> 'Unknown'
GROUP BY country
ORDER BY avg_depth_km DESC;

-- ============================================================
-- 26. Highest shallow-to-deep-focus ratio by country
-- Countries with zero deep events are shown as NULL rather than
-- infinite to avoid misleading ratios.
-- ============================================================
SELECT country,
       SUM(shallow_flag) AS shallow_events,
       SUM(deep_focus_flag) AS deep_events,
       ROUND(SUM(shallow_flag) /
             NULLIF(SUM(deep_focus_flag), 0), 2) AS shallow_deep_ratio
FROM earthquakes
WHERE country IS NOT NULL AND country <> 'Unknown'
GROUP BY country
HAVING SUM(deep_focus_flag) > 0
ORDER BY shallow_deep_ratio DESC;

-- ============================================================
-- 27. Average magnitude difference: tsunami vs non-tsunami
-- ============================================================
SELECT
    ROUND(AVG(CASE WHEN tsunami = 1 THEN mag END), 3) AS tsunami_avg_mag,
    ROUND(AVG(CASE WHEN tsunami = 0 THEN mag END), 3) AS non_tsunami_avg_mag,
    ROUND(
        AVG(CASE WHEN tsunami = 1 THEN mag END) -
        AVG(CASE WHEN tsunami = 0 THEN mag END), 3
    ) AS average_difference;

-- ============================================================
-- 28. Lowest data reliability using gap + RMS
-- quality_score is a project-defined analytical index, not USGS.
-- ============================================================
SELECT id, time, place, mag, nst, gap, rms,
       magError, depthError, quality_score
FROM earthquakes
ORDER BY quality_score ASC, gap DESC, rms DESC
LIMIT 20;

-- ============================================================
-- 29. Consecutive earthquakes within 50 km and 1 hour
-- MySQL 8 window functions + Haversine distance.
-- ============================================================
WITH ordered AS (
    SELECT
        id, time, latitude, longitude, place, mag,
        LEAD(id) OVER (ORDER BY time) AS next_id,
        LEAD(time) OVER (ORDER BY time) AS next_time,
        LEAD(latitude) OVER (ORDER BY time) AS next_latitude,
        LEAD(longitude) OVER (ORDER BY time) AS next_longitude
    FROM earthquakes
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL
),
distances AS (
    SELECT *,
        6371 * 2 * ASIN(
            SQRT(
                POWER(SIN(RADIANS(next_latitude - latitude) / 2), 2) +
                COS(RADIANS(latitude)) *
                COS(RADIANS(next_latitude)) *
                POWER(SIN(RADIANS(next_longitude - longitude) / 2), 2)
            )
        ) AS distance_km,
        TIMESTAMPDIFF(SECOND, time, next_time) AS seconds_apart
    FROM ordered
    WHERE next_time IS NOT NULL
)
SELECT id AS event_id,
       next_id AS next_event_id,
       time AS event_time,
       next_time,
       ROUND(distance_km, 2) AS distance_km,
       ROUND(seconds_apart / 60, 2) AS minutes_apart,
       mag
FROM distances
WHERE distance_km <= 50
  AND seconds_apart BETWEEN 0 AND 3600
ORDER BY event_time;

-- ============================================================
-- 30. Regions with highest frequency of deep-focus earthquakes
-- ============================================================
SELECT country,
       COUNT(*) AS deep_focus_events,
       ROUND(AVG(mag), 3) AS avg_magnitude,
       ROUND(AVG(depth_km), 2) AS avg_depth_km
FROM earthquakes
WHERE depth_km > 300
  AND country IS NOT NULL AND country <> 'Unknown'
GROUP BY country
ORDER BY deep_focus_events DESC
LIMIT 20;

SELECT id, time, place, mag, depth_km FROM earthquakes ORDER BY mag DESC LIMIT 10;

SELECT id, time, place, mag, depth_km FROM earthquakes ORDER BY depth_km DESC LIMIT 10;

SELECT * FROM earthquakes WHERE depth_km < 50 AND mag > 7.5 ORDER BY mag DESC;

SELECT country, AVG(depth_km) AS avg_depth_km
FROM earthquakes WHERE country <> 'Unknown'
GROUP BY country ORDER BY avg_depth_km DESC;

SELECT magType, AVG(mag) AS avg_magnitude, COUNT(*) AS events
FROM earthquakes GROUP BY magType ORDER BY events DESC;

SELECT year, COUNT(*) AS events
FROM earthquakes GROUP BY year ORDER BY events DESC;

SELECT month, month_name, COUNT(*) AS events
FROM earthquakes GROUP BY month, month_name ORDER BY events DESC;

SELECT day_of_week, COUNT(*) AS events
FROM earthquakes GROUP BY day_of_week ORDER BY events DESC;

SELECT hour, COUNT(*) AS events
FROM earthquakes GROUP BY hour ORDER BY hour;

SELECT net, COUNT(*) AS events
FROM earthquakes GROUP BY net ORDER BY events DESC LIMIT 10;

SELECT status, COUNT(*) AS events
FROM earthquakes GROUP BY status ORDER BY events DESC;

SELECT type, COUNT(*) AS events
FROM earthquakes GROUP BY type ORDER BY events DESC;

SELECT year, SUM(tsunami) AS tsunami_events
FROM earthquakes GROUP BY year ORDER BY year;

WITH yearly AS (
    SELECT year, COUNT(*) AS events FROM earthquakes GROUP BY year
)
SELECT year, events,
ROUND((events - LAG(events) OVER (ORDER BY year))
/ NULLIF(LAG(events) OVER (ORDER BY year), 0) * 100, 2) AS yoy_growth_pct
FROM yearly ORDER BY year;

SELECT country,
SUM(shallow_flag) AS shallow_events,
SUM(deep_focus_flag) AS deep_events,
ROUND(SUM(shallow_flag) / NULLIF(SUM(deep_focus_flag), 0), 2) AS shallow_deep_ratio
FROM earthquakes
WHERE country <> 'Unknown'
GROUP BY country ORDER BY shallow_deep_ratio DESC;

SELECT
AVG(CASE WHEN tsunami = 1 THEN mag END) AS tsunami_avg_mag,
AVG(CASE WHEN tsunami = 0 THEN mag END) AS non_tsunami_avg_mag,
AVG(CASE WHEN tsunami = 1 THEN mag END) - AVG(CASE WHEN tsunami = 0 THEN mag END) AS avg_difference
FROM earthquakes;

SELECT id, place, mag, gap, rms, nst, magError, depthError, quality_score
FROM earthquakes ORDER BY quality_score ASC LIMIT 20;

SELECT country, COUNT(*) AS deep_events, AVG(mag) AS avg_magnitude
FROM earthquakes WHERE depth_km > 300 AND country <> 'Unknown'
GROUP BY country ORDER BY deep_events DESC;

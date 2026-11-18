-- Run from the project folder with:
-- sqlite3 -header -column -readonly data/forecasting.sqlite3 < replenishment_report.sql

WITH latest_run AS (
    SELECT store_id, MAX(forecast_start) AS forecast_start
    FROM reorder_ranking
    GROUP BY store_id
)
SELECT
    r.priority,
    r.store_id,
    r.item_id,
    r.forecast_start AS week_start,
    ROUND(SUM(f.forecast_units), 2) AS forecast_week_units,
    r.inventory_position,
    r.reorder_point,
    r.gap AS units_below_reorder_point
FROM reorder_ranking AS r
JOIN latest_run AS latest
    ON latest.store_id = r.store_id
    AND latest.forecast_start = r.forecast_start
JOIN daily_forecasts AS f
    ON f.store_id = r.store_id
    AND f.item_id = r.item_id
    AND f.forecast_date >= r.forecast_start
    AND f.forecast_date < DATE(r.forecast_start, '+7 days')
WHERE r.decision = 'Reorder now'
GROUP BY
    r.priority, r.store_id, r.item_id, r.forecast_start,
    r.inventory_position, r.reorder_point, r.gap
ORDER BY r.store_id, r.priority;

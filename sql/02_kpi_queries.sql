USE sales_funnel_analytics;

-- A small lookup table so we can compare stages by their order in the
-- funnel, not just by name.
CREATE TABLE stage_order (
    stage_name VARCHAR(30) PRIMARY KEY,
    stage_num  INT NOT NULL
);

INSERT INTO stage_order VALUES
    ('Lead', 1),
    ('Contacted', 2),
    ('Demo Scheduled', 3),
    ('Demo Completed', 4),
    ('Proposal Sent', 5),
    ('Negotiation', 6),
    ('Closed', 7);

-- KPI 1: funnel - how many leads reached each stage or further
SELECT
    so.stage_name AS stage,
    COUNT(*) AS leads_reaching_or_beyond,
    ROUND(COUNT(*) / (SELECT COUNT(*) FROM leads) * 100, 1) AS pct_of_total
FROM stage_order so
JOIN leads l
    ON (SELECT stage_num FROM stage_order WHERE stage_name = l.stage_reached) >= so.stage_num
GROUP BY so.stage_name, so.stage_num
ORDER BY so.stage_num;

-- KPI 2: win rate by lead source
SELECT
    source,
    COUNT(*) AS total_leads,
    SUM(status = 'Won') AS won,
    ROUND(SUM(status = 'Won') / COUNT(*) * 100, 1) AS win_rate_pct
FROM leads
GROUP BY source
ORDER BY win_rate_pct DESC;

USE sales_funnel_analytics;

-- KPI 3: speed-to-lead effect on win rate
SELECT
    CASE
        WHEN response_time_hours <= 1  THEN '1. Under 1 hour'
        WHEN response_time_hours <= 24 THEN '2. 1-24 hours'
        WHEN response_time_hours <= 72 THEN '3. 1-3 days'
        ELSE '4. Over 3 days'
    END AS response_bucket,
    COUNT(*) AS total_leads,
    SUM(status = 'Won') AS won,
    ROUND(SUM(status = 'Won') / COUNT(*) * 100, 1) AS win_rate_pct
FROM leads
GROUP BY response_bucket
ORDER BY response_bucket;

-- KPI 4: lost pipeline value by reason
SELECT
    lost_reason,
    COUNT(*) AS lost_deals,
    SUM(deal_value) AS total_lost_value,
    ROUND(AVG(deal_value), 2) AS avg_lost_value
FROM leads
WHERE status = 'Lost' AND lost_reason IS NOT NULL
GROUP BY lost_reason
ORDER BY total_lost_value DESC;

-- KPI 5: rep leaderboard
SELECT
    rep,
    COUNT(*) AS total_leads,
    SUM(status = 'Won') AS won,
    ROUND(SUM(status = 'Won') / COUNT(*) * 100, 1) AS win_rate_pct,
    ROUND(SUM(CASE WHEN status = 'Won' THEN deal_value ELSE 0 END), 2) AS total_revenue
FROM leads
GROUP BY rep
ORDER BY total_revenue DESC;
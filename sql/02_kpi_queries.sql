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
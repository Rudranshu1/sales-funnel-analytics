CREATE DATABASE IF NOT EXISTS sales_funnel_analytics;
USE sales_funnel_analytics;

CREATE TABLE leads (
    lead_id              VARCHAR(20)   PRIMARY KEY,
    created_at           DATETIME      NOT NULL,
    source               VARCHAR(50)   NOT NULL,
    product              VARCHAR(50)   NOT NULL,
    region               VARCHAR(50)   NOT NULL,
    rep                  VARCHAR(20)   NOT NULL,
    response_time_hours  DECIMAL(10,2) NOT NULL,
    stage_reached        VARCHAR(30)   NOT NULL,
    status               VARCHAR(10)   NOT NULL,
    lost_reason          VARCHAR(50),
    deal_value           DECIMAL(10,2),
    closed_at            DATETIME
);

SET GLOBAL local_infile = 1;

LOAD DATA LOCAL INFILE 'D:/Projects/MyGitHubProject/Project2-Rebuild/data/leads_cleaned.csv'
INTO TABLE leads
FIELDS TERMINATED BY ','
OPTIONALLY ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(lead_id, created_at, source, product, region, rep, response_time_hours, stage_reached, status, @lost_reason, @deal_value, @closed_at)
SET
    lost_reason = NULLIF(@lost_reason, ''),
    deal_value  = NULLIF(@deal_value, ''),
    closed_at   = NULLIF(@closed_at, '');

SELECT COUNT(*) AS total_rows FROM leads;
SELECT status, COUNT(*) FROM leads GROUP BY status;
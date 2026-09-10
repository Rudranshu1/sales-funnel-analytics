"""
Synthetic sales lead / funnel data generator - Project 2 (Sales Funnel Analytics).

Models an edtech-style inside-sales funnel, in the same spirit as the
business-development work at Byju's: a lead comes in, gets contacted, gets a
demo scheduled, the demo happens, a proposal goes out, negotiation happens,
and the deal closes won or lost - or it just goes cold partway through,
which is exactly what a real CRM funnel looks like.

Fully synthetic - no real company, prospect, or customer data anywhere.
Every number below is a documented assumption, not a random guess: source
quality, rep skill, and response speed all deliberately shape the win rate,
so the "why" behind the funnel's shape is explainable, not just observed.

Run: python generate_data.py   (from inside the data/ folder)
Output: leads_clean.csv  (~7,000 rows, Jan 2025 - Jun 2026)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

rng = np.random.default_rng(7)

N_LEADS = 7000
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2026, 6, 30)
TOTAL_DAYS = (END_DATE - START_DATE).days

# lead sources: weight = share of total lead volume, quality = a multiplier
# on how likely that source's leads are to convert (referral/webinar leads
# run warmer than cold outreach)
SOURCES = ["Organic Search", "Paid Search", "Social Media", "Referral", "Webinar", "Cold Outreach", "Partner Channel"]
SOURCE_WEIGHTS = [0.22, 0.20, 0.16, 0.14, 0.10, 0.10, 0.08]
SOURCE_QUALITY = {
    "Organic Search": 1.05, "Paid Search": 0.90, "Social Media": 0.80,
    "Referral": 1.45, "Webinar": 1.30, "Cold Outreach": 0.55, "Partner Channel": 1.15,
}

PRODUCTS = ["K-12 Math", "Competitive Exam Prep", "Coding for Kids", "Language Learning", "Study Abroad Prep"]
PRODUCT_WEIGHTS = [0.28, 0.24, 0.20, 0.16, 0.12]
PRODUCT_PRICE = {
    "K-12 Math": 480, "Competitive Exam Prep": 950, "Coding for Kids": 620,
    "Language Learning": 340, "Study Abroad Prep": 1400,
}

REGIONS = ["North Region", "South Region", "West Region", "East Region", "International"]
REGION_WEIGHTS = [0.24, 0.28, 0.22, 0.16, 0.10]

REPS = [f"Rep_{i:02d}" for i in range(1, 16)]
rep_skill = {r: float(np.clip(rng.normal(1.0, 0.25), 0.5, 1.7)) for r in REPS}
rep_region = {r: REGIONS[i % len(REGIONS)] for i, r in enumerate(REPS)}

LOST_REASONS = ["Price Objection", "Went With Competitor", "Bad Timing", "No Response / Ghosted", "Budget Not Approved"]
LOST_REASON_WEIGHTS = [0.30, 0.18, 0.20, 0.22, 0.10]

# base probability of surviving each stage transition, BEFORE the
# source/rep/speed adjustment below - tuned so the funnel shape resembles a
# real one (steepest drop right after first contact, gentler after a demo
# actually happens)
TRANSITIONS = [
    ("Lead", "Contacted", 0.78),
    ("Contacted", "Demo Scheduled", 0.38),
    ("Demo Scheduled", "Demo Completed", 0.82),
    ("Demo Completed", "Proposal Sent", 0.62),
    ("Proposal Sent", "Negotiation", 0.58),
    ("Negotiation", "Closed Won", 0.42),
]

rows = []
for i in range(N_LEADS):
    lead_id = f"LD-{300000 + i}"

    day_offset = int(rng.integers(0, TOTAL_DAYS))
    created_at = START_DATE + timedelta(days=day_offset, hours=int(rng.integers(7, 21)), minutes=int(rng.integers(0, 60)))
    if created_at.weekday() >= 5 and rng.random() < 0.6:
        created_at = created_at - timedelta(days=created_at.weekday() - 4)

    source = str(rng.choice(SOURCES, p=SOURCE_WEIGHTS))
    product = str(rng.choice(PRODUCTS, p=PRODUCT_WEIGHTS))
    region = str(rng.choice(REGIONS, p=REGION_WEIGHTS))

    candidates = [r for r in REPS if rep_region[r] == region]
    rep = str(rng.choice(candidates)) if candidates else str(rng.choice(REPS))
    skill = rep_skill[rep]
    quality = SOURCE_QUALITY[source]

    # response time in hours: faster for skilled reps, with a long right
    # tail (most leads get called back quickly, a few sit for days)
    response_hours = max(0.05, float(rng.lognormal(mean=1.1 - 0.35 * (skill - 1), sigma=0.9)))
    # speed-to-lead effect: a fast first response boosts every downstream
    # transition, a slow one drags all of them down
    if response_hours <= 1:
        speed_multiplier = 1.35
    elif response_hours <= 24:
        speed_multiplier = 1.15
    elif response_hours <= 72:
        speed_multiplier = 0.85
    else:
        speed_multiplier = 0.35

    combined_multiplier = quality * skill * speed_multiplier

    stage_reached = "Lead"
    status = "Open"
    lost_reason = ""
    closed_at = None
    days_elapsed = response_hours / 24

    for frm, to, base_p in TRANSITIONS:
        p = float(np.clip(base_p * combined_multiplier, 0.02, 0.97))
        if rng.random() < p:
            days_elapsed += float(rng.uniform(1, 12))
            if to == "Closed Won":
                stage_reached = "Closed"
                status = "Won"
                closed_at = created_at + timedelta(days=days_elapsed)
                break
            stage_reached = to
        else:
            stage_reached = frm
            if frm in ("Demo Completed", "Proposal Sent", "Negotiation"):
                status = "Lost"
                lost_reason = str(rng.choice(LOST_REASONS, p=LOST_REASON_WEIGHTS))
                days_elapsed += float(rng.uniform(2, 20))
                closed_at = created_at + timedelta(days=days_elapsed)
            break

    base_price = PRODUCT_PRICE[product]
    if status == "Won" or (status == "Lost" and stage_reached in ("Demo Completed", "Proposal Sent", "Negotiation")):
        deal_value = round(base_price * float(rng.uniform(0.85, 1.25)), 2)
    else:
        deal_value = np.nan

    rows.append({
        "lead_id": lead_id,
        "created_at": created_at,
        "source": source,
        "product": product,
        "region": region,
        "rep": rep,
        "response_time_hours": round(response_hours, 2),
        "stage_reached": stage_reached,
        "status": status,
        "lost_reason": lost_reason,
        "deal_value": deal_value,
        "closed_at": closed_at,
    })

df = pd.DataFrame(rows)
df.to_csv("leads_clean.csv", index=False)

print(f"Generated {len(df)} leads -> leads_clean.csv")
print()
print("status breakdown:")
print(df["status"].value_counts())
print()
print("stage_reached breakdown:")
print(df["stage_reached"].value_counts())
print()
print("win rate by source:")
print(df.groupby("source")["status"].apply(lambda s: (s == "Won").mean()).round(3).sort_values(ascending=False))

"""
Turns the clean synthetic leads.csv into something that looks like a real,
slightly broken CRM export - the same kind of mess you'd actually get
pulling data out of a system like this in a real job.

Injected issues (each one is a real thing that happens in CRM exports):
- ~1.5% duplicate rows (a sync job double-fired and re-inserted some leads)
- ~6% of region values missing (reps sometimes skip optional fields)
- inconsistent casing / abbreviations on source and product (different
  people/integrations wrote them differently over 18 months)
- created_at stored in three different date formats (an export format
  changed partway through the period, or two systems feed the same field)
- deal_value stored as a currency-formatted string ("$480.00") for a chunk
  of rows, instead of a plain number
- a handful of negative response_time_hours (a manual data-entry error)

Run: python messify.py   (from inside the data/ folder, after generate_data.py)
Input:  leads_clean.csv
Output: leads_raw.csv
"""

import numpy as np
import pandas as pd

rng = np.random.default_rng(13)

df = pd.read_csv("leads_clean.csv")

# --- 1. duplicate rows (sync double-fire) ---
n_dupes = int(len(df) * 0.015)
dupe_rows = df.sample(n=n_dupes, random_state=13)
df = pd.concat([df, dupe_rows], ignore_index=True)

# --- 2. missing region values ---
missing_region_idx = df.sample(frac=0.06, random_state=14).index
df.loc[missing_region_idx, "region"] = np.nan

# --- 3. inconsistent casing / abbreviations on source and product ---
SOURCE_VARIANTS = {
    "Organic Search": ["organic search", "Organic search", "SEO"],
    "Paid Search": ["paid search", "PPC", "Paid  Search"],
    "Social Media": ["social media", "Social", "SOCIAL MEDIA"],
    "Cold Outreach": ["cold outreach", "Cold-Outreach", "COLD OUTREACH"],
}
PRODUCT_VARIANTS = {
    "K-12 Math": ["k-12 math", "K12 Math", "K-12  Math"],
    "Coding for Kids": ["coding for kids", "Coding For Kids", "CODING FOR KIDS"],
}


def messify_category(value, variants_map, messy_frac=0.15):
    if value in variants_map and rng.random() < messy_frac:
        return rng.choice(variants_map[value])
    return value


df["source"] = df["source"].apply(lambda v: messify_category(v, SOURCE_VARIANTS))
df["product"] = df["product"].apply(lambda v: messify_category(v, PRODUCT_VARIANTS))

# --- 4. mixed date formats on created_at ---
def mixed_date_format(dt_str, roll):
    dt = pd.to_datetime(dt_str)
    if roll < 0.34:
        return dt.strftime("%m/%d/%Y %H:%M")       # 03/14/2025 09:15
    elif roll < 0.67:
        return dt.strftime("%d-%b-%Y %H:%M")        # 14-Mar-2025 09:15
    else:
        return dt.strftime("%Y-%m-%d %H:%M:%S")     # ISO-ish, left mostly alone


rolls = rng.random(len(df))
df["created_at"] = [mixed_date_format(v, r) for v, r in zip(df["created_at"], rolls)]

# --- 5. deal_value as a currency string for a subset of non-null rows ---
def currency_string(v, roll):
    if pd.isna(v):
        return v
    if roll < 0.30:
        return f"${v:,.2f}"
    return v


rolls2 = rng.random(len(df))
df["deal_value"] = [currency_string(v, r) for v, r in zip(df["deal_value"], rolls2)]

# --- 6. a few negative response_time_hours entry errors ---
neg_idx = df.sample(n=12, random_state=15).index
df.loc[neg_idx, "response_time_hours"] = -df.loc[neg_idx, "response_time_hours"]

df.to_csv("leads_raw.csv", index=False)

print(f"leads_raw.csv written: {len(df)} rows (started from {len(df) - n_dupes} clean rows)")
print(f"duplicates added: {n_dupes}")
print(f"missing region: {df['region'].isna().sum()}")
print(f"negative response_time_hours: {(pd.to_numeric(df['response_time_hours'], errors='coerce') < 0).sum()}")
print()
print("sample of messy source/product values now present:")
print(sorted(df["source"].unique()))
print(sorted(df["product"].unique()))
print()
print("sample deal_value entries (mixed types):")
print(df["deal_value"].dropna().sample(6, random_state=1).tolist())

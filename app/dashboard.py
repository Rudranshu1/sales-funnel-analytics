"""
Interactive dashboard - Project 2 (Sales Funnel Analytics), Lesson 5.

Same data and charts as notebooks/02_analysis_and_charts.ipynb, but live:
sidebar filters (date range, source, region, rep) instantly recompute every
KPI and redraw every chart.

Run: streamlit run app/dashboard.py   (from the project root, venv active)
"""
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("Sales Funnel Analytics")

@st.cache_data

def load_data():
    return pd.read_csv("data/leads_cleaned.csv", parse_dates=["created_at", "closed_at"])
BLUE = "#2a78d6"
ORANGE = "#eb6834"
STAGE_ORDER = {
    "Lead": 1, "Contacted": 2, "Demo Scheduled": 3, "Demo Completed": 4,
    "Proposal Sent": 5, "Negotiation": 6, "Closed": 7,
}

def funnel_chart(data):
    total = len(data)
    stage_num = data["stage_reached"].map(STAGE_ORDER)
    values = [(stage_num >= n).sum() / total * 100 for n in STAGE_ORDER.values()]

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(list(STAGE_ORDER.keys()), values, color=BLUE)
    ax.invert_yaxis()
    for i, v in enumerate(values):
        ax.text(v + 1.5, i, f"{v:.1f}%", va="center", fontsize=9)
    ax.set_xlim(0, 110)
    ax.set_title("Funnel: where deals fall off")
    fig.tight_layout()
    return fig

def win_rate_by_source_chart(data):
    g = data.groupby("source")["status"].apply(lambda s: (s == "Won").mean() * 100).sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(7, 4))
    colors = [ORANGE if i == 0 else BLUE for i in range(len(g))]
    ax.bar(g.index, g.values, color=colors)
    for i, v in enumerate(g.values):
        ax.text(i, v + 0.5, f"{v:.1f}%", ha="center", fontsize=9)
    ax.set_title("Win rate by source")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    fig.tight_layout()
    return fig


def speed_to_lead_chart(data):
    def bucket(h):
        if h <= 1: return "1. Under 1 hour"
        if h <= 24: return "2. 1-24 hours"
        if h <= 72: return "3. 1-3 days"
        return "4. Over 3 days"

    b = data["response_time_hours"].apply(bucket)
    g = data.groupby(b)["status"].apply(lambda s: (s == "Won").mean() * 100)
    labels = [i.split(". ")[1] for i in g.index]
    fig, ax = plt.subplots(figsize=(7, 4))
    colors = [ORANGE if i == 0 else BLUE for i in range(len(g))]
    ax.bar(labels, g.values, color=colors)
    for i, v in enumerate(g.values):
        ax.text(i, v + 0.5, f"{v:.1f}%", ha="center", fontsize=9)
    ax.set_title("Speed-to-lead: response time vs. win rate")
    fig.tight_layout()
    return fig


def lost_value_chart(data):
    lost = data[data["status"] == "Lost"]
    g = lost.groupby("lost_reason")["deal_value"].sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.barh(g.index, g.values, color=BLUE)
    ax.invert_yaxis()
    ax.set_title("Lost pipeline value by reason")
    fig.tight_layout()
    return fig


def rep_leaderboard_chart(data):
    won_value = data["deal_value"].where(data["status"] == "Won", 0)
    g = won_value.groupby(data["rep"]).sum().sort_values(ascending=False)
    fig, ax = plt.subplots(figsize=(9, 5))
    colors = [ORANGE] + [BLUE] * (len(g) - 1)
    ax.barh(g.index, g.values, color=colors)
    ax.invert_yaxis()
    ax.set_title("Rep leaderboard by revenue won")
    fig.tight_layout()
    return fig


def monthly_trend_chart(data):
    month = data["created_at"].dt.to_period("M").dt.to_timestamp()
    monthly = data.groupby(month).agg(
        leads=("lead_id", "count"),
        win_rate_pct=("status", lambda s: (s == "Won").mean() * 100),
    )
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 5), sharex=True)
    ax1.bar(monthly.index, monthly["leads"], color=BLUE, width=20)
    ax1.set_ylabel("Leads created")
    ax1.set_title("Monthly lead volume and win rate")
    ax2.plot(monthly.index, monthly["win_rate_pct"], color=BLUE, marker="o", markersize=4)
    ax2.set_ylabel("Win rate (%)")
    fig.tight_layout()
    return fig


def show(fig):
    st.pyplot(fig)
    plt.close(fig)

df = load_data()
st.write(f"Loaded {len(df):,} leads")

sources = st.sidebar.multiselect(
    "Source", options=sorted(df["source"].unique()), default=sorted(df["source"].unique())
)
regions = st.sidebar.multiselect(
    "Region", options=sorted(df["region"].unique()), default=sorted(df["region"].unique())
)
reps = st.sidebar.multiselect(
    "Rep", options=sorted(df["rep"].unique()), default=sorted(df["rep"].unique())
)

min_date = df["created_at"].min().date()
max_date = df["created_at"].max().date()
date_range = st.sidebar.date_input(
    "Created between", value=(min_date, max_date), min_value=min_date, max_value=max_date
)

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range[0]
mask = (
    (df["created_at"].dt.date >= start_date)
    & (df["created_at"].dt.date <= end_date)
    & df["source"].isin(sources)
    & df["region"].isin(regions)
    & df["rep"].isin(reps)
)
fdf = df[mask]

st.write(f"{len(fdf):,} of {len(df):,} leads match your filter")
st.dataframe(fdf.head(10))
if fdf.empty:
    st.warning("No leads match these filters — widen your selections in the sidebar.")
    st.stop()

won = (fdf["status"] == "Won")
win_rate = won.mean() * 100
revenue = fdf.loc[won, "deal_value"].sum()
avg_deal = fdf.loc[won, "deal_value"].mean() if won.any() else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Leads", f"{len(fdf):,}")
c2.metric("Win rate", f"{win_rate:.1f}%")
c3.metric("Revenue won", f"${revenue:,.0f}")
c4.metric("Avg deal size", f"${avg_deal:,.0f}" if won.any() else "-")

row1a, row1b = st.columns(2)
with row1a:
    show(funnel_chart(fdf))
with row1b:
    show(win_rate_by_source_chart(fdf))

row2a, row2b = st.columns(2)
with row2a:
    show(speed_to_lead_chart(fdf))
with row2b:
    show(lost_value_chart(fdf))

show(rep_leaderboard_chart(fdf))
show(monthly_trend_chart(fdf))
import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import text

from app.db import engine

st.set_page_config(
    page_title="E-Commerce Pricing & Market Intelligence",
    page_icon="🏷️",
    layout="wide",
)

# ---------------------------------------------------------------
# Data loading — pulls straight from the pipeline's SQLite DB
# ---------------------------------------------------------------
@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    query = text("""
        SELECT
            p.name AS product,
            p.brand AS brand,
            c.name AS category,
            pl.name AS platform,
            s.mrp AS mrp,
            s.selling_price AS selling_price,
            s.rating AS rating,
            s.is_verified_real AS verified,
            s.observed_at AS observed_at,
            s.source AS source
        FROM price_snapshots s
        JOIN products p ON p.id = s.product_id
        JOIN categories c ON c.id = p.category_id
        JOIN platforms pl ON pl.id = s.platform_id
    """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    df["observed_at"] = pd.to_datetime(df["observed_at"])
    df["verified"] = df["verified"].astype(bool)
    df["discount_pct"] = (df["mrp"] - df["selling_price"]) / df["mrp"]
    return df


df = load_data()

# ---------------------------------------------------------------
# Header
# ---------------------------------------------------------------
st.title("🏷️ What's Actually on Sale Across Indian E-Commerce?")
st.caption(
    f"Cross-platform pricing & discount intelligence · {df['platform'].nunique()} marketplaces · "
    f"{df['category'].nunique()} categories · {len(df):,} tracked listings. "
    "Data served live from the pipeline's SQLite database (`ecom.db`), not a static file."
)

verified_count = int(df["verified"].sum())
if verified_count:
    st.info(
        f"✅ {verified_count} listings below are **hand-verified real prices** looked up individually from "
        f"Amazon.in/Flipkart (see the 'source' column). The rest is a synthetic sample built to mirror "
        f"realistic cross-platform discount patterns for portfolio/demo purposes.",
        icon="✅",
    )

# ---------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------
st.sidebar.header("Filters")
categories = ["All"] + sorted(df["category"].unique().tolist())
platforms = ["All"] + sorted(df["platform"].unique().tolist())

sel_category = st.sidebar.selectbox("Category", categories)
sel_platform = st.sidebar.selectbox("Platform", platforms)
search = st.sidebar.text_input("Search product name")
verified_only = st.sidebar.checkbox("Verified real listings only", value=False)

filtered = df.copy()
if sel_category != "All":
    filtered = filtered[filtered["category"] == sel_category]
if sel_platform != "All":
    filtered = filtered[filtered["platform"] == sel_platform]
if search:
    filtered = filtered[filtered["product"].str.contains(search, case=False, na=False)]
if verified_only:
    filtered = filtered[filtered["verified"]]

# Latest snapshot per product+platform, to avoid double-counting weekly history in KPIs/tables
latest = (
    filtered.sort_values("observed_at")
    .groupby(["product", "platform"], as_index=False)
    .last()
)

# ---------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Listings tracked", f"{len(latest):,}")
col2.metric("Avg discount", f"{latest['discount_pct'].mean() * 100:.1f}%" if len(latest) else "—")
top_platform = (
    latest.groupby("platform")["discount_pct"].mean().sort_values(ascending=False)
    if len(latest) else pd.Series(dtype=float)
)
col3.metric(
    "Deepest discount platform",
    top_platform.index[0] if len(top_platform) else "—",
    f"{top_platform.iloc[0] * 100:.1f}% avg off" if len(top_platform) else "",
)
col4.metric("Verified real listings", int(latest["verified"].sum()) if len(latest) else 0)

st.divider()

# ---------------------------------------------------------------
# Charts
# ---------------------------------------------------------------
c1, c2 = st.columns(2)

with c1:
    st.subheader("Avg discount by platform")
    plat_summary = (
        df.groupby("platform")["discount_pct"].mean().reset_index().sort_values("discount_pct", ascending=False)
    )
    fig = px.bar(
        plat_summary, x="platform", y="discount_pct",
        text_auto=".1%", color="platform",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_layout(yaxis_tickformat=".0%", showlegend=False, yaxis_title="Avg discount %", xaxis_title="")
    st.plotly_chart(fig, width="stretch")

with c2:
    st.subheader("Avg discount by category")
    cat_summary = (
        df.groupby("category")["discount_pct"].mean().reset_index().sort_values("discount_pct", ascending=False)
    )
    fig2 = px.bar(
        cat_summary, x="discount_pct", y="category", orientation="h",
        text_auto=".1%", color="category",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig2.update_layout(xaxis_tickformat=".0%", showlegend=False, xaxis_title="Avg discount %", yaxis_title="")
    st.plotly_chart(fig2, width="stretch")

st.subheader("Weekly average discount trend")
weekly = (
    df[~df["verified"]]
    .assign(week=df["observed_at"].dt.strftime("%Y-%m-%d"))
    .groupby("week")["discount_pct"].mean().reset_index()
    .sort_values("week")
)
fig3 = px.line(weekly, x="week", y="discount_pct", markers=True)
fig3.update_layout(yaxis_tickformat=".0%", yaxis_title="Avg discount %", xaxis_title="Week starting")
st.plotly_chart(fig3, width="stretch")

st.divider()

# ---------------------------------------------------------------
# Listings table
# ---------------------------------------------------------------
st.subheader(f"Listings explorer ({len(latest):,} matching)")

display_df = latest.sort_values("discount_pct", ascending=False)[
    ["product", "platform", "category", "mrp", "selling_price", "discount_pct", "rating", "verified", "source"]
].copy()
display_df["discount_pct"] = (display_df["discount_pct"] * 100).round(1).astype(str) + "%"
display_df["mrp"] = display_df["mrp"].apply(lambda x: f"₹{x:,.0f}")
display_df["selling_price"] = display_df["selling_price"].apply(lambda x: f"₹{x:,.0f}")
display_df = display_df.rename(columns={
    "product": "Product", "platform": "Platform", "category": "Category",
    "mrp": "MRP", "selling_price": "Price", "discount_pct": "Discount",
    "rating": "Rating", "verified": "Verified Real", "source": "Source",
})

st.dataframe(display_df, width="stretch", height=420, hide_index=True)

st.caption(
    "Built with a real pipeline: SQLite database + validated ingestion (see `app/pipeline/`) — "
    "not a static spreadsheet dump. Re-run `python3 bootstrap.py` after adding a real scraper/API "
    "source to `app/pipeline/` to refresh with live data."
)

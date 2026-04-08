import streamlit as st
import pandas as pd
from components.api_client import api_get
from components.charts import spend_line_chart

st.set_page_config(page_title="Overview", layout="wide")
st.title("Platform overview")
st.caption(f"All tenants — month-to-date")

# --- Metric cards ---
try:
    summary = api_get("/usage/platform-summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Platform spend (MTD)", f"${summary['total_spend_mtd']:.2f}")
    col2.metric("Active tenants",       summary["active_tenants"])
    col3.metric("API calls today",      f"{summary['calls_today']:,}")
    col4.metric("Avg cost / request",   f"${summary['avg_cost_per_request']:.5f}")
except Exception as e:
    st.error(f"Could not load summary: {e}")

st.divider()

# --- Daily spend chart ---
st.subheader("Daily spend by tenant (last 30 days)")
try:
    daily_data = api_get("/usage/platform-daily")
    st.plotly_chart(spend_line_chart(daily_data), use_container_width=True)
except Exception as e:
    st.warning(f"Chart unavailable: {e}")

st.divider()

# --- Anomaly alerts ---
st.subheader("Recent anomaly alerts")
try:
    anomalies = api_get("/ai/platform-anomalies")
    if anomalies:
        st.error(f"{len(anomalies)} anomaly alert(s) detected in the last 24 hours")
        for a in anomalies:
            st.warning(
                f"Tenant **{a['tenant_id']}**: {a['deviation_pct']:+.1f}% above average on {a['date']} "
                f"(severity: {a['severity']})"
            )
    else:
        st.success("No anomalies detected in the last 24 hours.")
except Exception as e:
    st.warning(f"Anomaly data unavailable: {e}")

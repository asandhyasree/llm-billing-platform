import streamlit as st
from components.api_client import api_get, api_post

st.set_page_config(page_title="AI Insights", layout="wide")
st.title("AI insights")

# --- Tenant selector ---
try:
    tenants = api_get("/tenants")
    tenant_map = {t["name"]: t["id"] for t in tenants}
except Exception as e:
    st.error(f"Could not load tenants: {e}")
    st.stop()

if not tenant_map:
    st.info("No tenants found. Create one via the API first.")
    st.stop()

tenant_id = tenant_map[st.selectbox("Tenant", list(tenant_map.keys()))]

# --- Anomaly section ---
st.subheader("Anomaly detection")
try:
    anomalies = api_get(f"/ai/anomalies/{tenant_id}")
    st.caption(f"{len(anomalies)} flagged day(s)")

    for a in anomalies:
        icon = "🔴" if a["severity"] == "high" else "🟡"
        with st.expander(f"{icon} {a['date']} — ${a['total_cost']:.4f} ({a['deviation_pct']:+.1f}% vs avg)"):
            col1, col2, col3 = st.columns(3)
            col1.metric("Input tokens",  f"{a['input_tokens']:,}")
            col2.metric("Output tokens", f"{a['output_tokens']:,}")
            col3.metric("Z-score",       a["z_score"])
            st.markdown(f"**Model:** {a['model']}  |  **Severity:** {a['severity']}")

            if st.button("Explain this anomaly", key=f"explain-{a['date']}"):
                with st.spinner("Generating explanation..."):
                    result = api_post("/ai/explain", {"anomaly": a})
                    st.info(result["explanation"])
except Exception as e:
    st.warning(f"Anomaly data unavailable: {e}")

st.divider()

# --- Spend forecast ---
st.subheader("Spend forecast")
try:
    forecast = api_get(f"/ai/forecast/{tenant_id}")
    if "error" not in forecast:
        col1, col2, col3 = st.columns(3)
        col1.metric("Spent so far",          f"${forecast['spent_so_far_usd']:.2f}")
        col2.metric("Projected remaining",   f"${forecast['projected_remaining_usd']:.2f}")
        col3.metric("Projected month total", f"${forecast['projected_month_total_usd']:.2f}")
        st.caption(f"Trend: **{forecast['trend']}** | Based on {forecast['days_of_data']} days of data")
    else:
        st.info(forecast["error"])
except Exception as e:
    st.warning(f"Forecast unavailable: {e}")

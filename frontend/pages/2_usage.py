import streamlit as st
import pandas as pd
from components.api_client import api_get
from components.charts import model_bar_chart

st.set_page_config(page_title="Usage Explorer", layout="wide")
st.title("Usage explorer")

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

selected_name = st.selectbox("Tenant", list(tenant_map.keys()))
tenant_id = tenant_map[selected_name]

# --- Filters ---
col1, col2 = st.columns(2)
start_date = col1.date_input("Start date", value=None)
end_date   = col2.date_input("End date", value=None)

# --- Token breakdown by model ---
st.subheader("Token usage by model")
try:
    model_data = api_get(f"/usage/{tenant_id}/usage/by-model")
    st.plotly_chart(model_bar_chart(model_data), use_container_width=True)
except Exception as e:
    st.warning(f"Model breakdown unavailable: {e}")

st.divider()

# --- Raw usage events table ---
st.subheader("Usage events")
try:
    params = {}
    if start_date is not None:
        params["start"] = str(start_date)
    if end_date is not None:
        params["end"] = f"{end_date}T23:59:59"

    events = api_get(f"/usage/{tenant_id}/usage", params=params)
    if events:
        df = pd.DataFrame(events)
        display_cols = ["ts", "model", "provider", "input_tokens", "output_tokens", "total_cost_usd", "billed_cost_usd"]
        st.dataframe(df[[c for c in display_cols if c in df.columns]], use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, file_name=f"{selected_name}_usage.csv", mime="text/csv")
    else:
        st.info("No usage events found for this period.")
except Exception as e:
    st.warning(f"Events unavailable: {e}")

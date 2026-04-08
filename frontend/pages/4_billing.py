import streamlit as st
import pandas as pd
from datetime import datetime
from components.api_client import api_get, api_post

st.set_page_config(page_title="Billing", layout="wide")
st.title("Billing")

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

# --- Credit balance ---
st.subheader("Credit balance")
try:
    credits = api_get(f"/billing/{tenant_id}/credits")
    balance = credits["balance_usd"]

    col1, col2 = st.columns([1, 2])
    col1.metric("Current balance", f"${balance:.4f}")

    with col2:
        with st.form("topup_form"):
            amount = st.number_input("Add credits (USD)", min_value=1.0, step=10.0)
            note   = st.text_input("Note (optional)")
            if st.form_submit_button("Top up"):
                result = api_post(f"/billing/{tenant_id}/credits/topup", {"amount_usd": amount, "note": note})
                st.success(f"Credits added. New balance: ${result['new_balance_usd']:.4f}")
                st.rerun()

    if credits.get("ledger"):
        st.subheader("Ledger history")
        df = pd.DataFrame(credits["ledger"])
        st.dataframe(df[["ts", "event_type", "amount_usd", "note"]], use_container_width=True)
except Exception as e:
    st.warning(f"Credit data unavailable: {e}")

st.divider()

# --- Invoice preview ---
st.subheader("Invoice preview")
now = datetime.utcnow()
col1, col2 = st.columns(2)
year  = col1.number_input("Year",  value=now.year,  min_value=2024)
month = col2.number_input("Month", value=now.month, min_value=1, max_value=12)

try:
    invoice = api_get(f"/billing/{tenant_id}/invoice/preview", params={"year": year, "month": month})
    st.metric("Total billed", f"${invoice['total_billed']:.4f}")
    if invoice["line_items"]:
        df = pd.DataFrame(invoice["line_items"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No usage for this period.")
except Exception as e:
    st.warning(f"Invoice unavailable: {e}")

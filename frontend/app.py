import streamlit as st

st.set_page_config(
    page_title="LLM Billing Platform",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("LLM Billing & Observability Platform")
st.markdown(
    """
    Welcome to the admin dashboard. Use the sidebar to navigate:

    - **Tenants** — Create and manage tenants
    - **Overview** — Platform KPIs, spend chart, and anomaly alerts
    - **Usage** — Explore usage events per tenant with filters
    - **AI Insights** — Anomaly detection, spend forecast, RAG explanations
    - **Billing** — Credit balances, top-ups, and invoice previews
    - **Chat** — Ask your usage data in plain English
    """
)

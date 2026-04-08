import streamlit as st
import pandas as pd
from components.api_client import api_get, api_post

st.set_page_config(page_title="Tenants", layout="wide")
st.title("Tenant management")

# --- Create tenant ---
st.subheader("Create a new tenant")

with st.form("create_tenant"):
    name = st.text_input("Name", placeholder="Acme Corp")
    email = st.text_input("Email", placeholder="contact@acme.com")
    tier = st.selectbox("Tier", ["basic", "pro", "enterprise"])
    markup_pct = st.number_input("Markup %", min_value=0.0, max_value=100.0, value=20.0, step=1.0)
    submitted = st.form_submit_button("Create tenant")

if submitted:
    if not name:
        st.error("Name is required.")
    else:
        try:
            result = api_post("/tenants", {
                "name": name,
                "email": email or None,
                "tier": tier,
                "markup_pct": markup_pct,
            })
            st.success(f"Tenant **{name}** created!")
            st.code(result["api_key"], language=None)
            st.caption(f"Tenant ID: {result['tenant']['id']}")
        except Exception as e:
            st.error(f"Failed to create tenant: {e}")

st.divider()

# --- Existing tenants ---
st.subheader("Existing tenants")

try:
    tenants = api_get("/tenants")
    if tenants:
        df = pd.DataFrame(tenants)
        display_cols = ["id", "name", "email", "tier", "markup_pct", "created_at"]
        st.dataframe(df[[c for c in display_cols if c in df.columns]], use_container_width=True)

        # --- API keys per tenant ---
        st.divider()
        st.subheader("API keys")
        for t in tenants:
            try:
                keys = api_get(f"/tenants/{t['id']}/keys")
                if keys:
                    for k in keys:
                        st.text_input(
                            f"{t['name']} — {k['label']}",
                            value=k["api_key"] or "Key not stored (created before this feature)",
                            disabled=True,
                            key=f"key_{t['id']}_{k['label']}",
                        )
            except Exception:
                pass
    else:
        st.info("No tenants yet. Create one above.")
except Exception as e:
    st.error(f"Could not load tenants: {e}")

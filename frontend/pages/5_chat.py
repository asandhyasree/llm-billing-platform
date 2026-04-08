import streamlit as st
from components.api_client import api_get, api_post

st.set_page_config(page_title="Chat", layout="wide")
st.title("Ask your usage data")

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

st.caption("Ask questions in plain English — e.g. 'Which model cost the most last week?' or 'How many requests did I make in March?'")

if "messages" not in st.session_state:
    st.session_state.messages = []

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg.get("sql"):
            with st.expander("View SQL"):
                st.code(msg["sql"], language="sql")
        if msg.get("rows"):
            with st.expander("View raw data"):
                st.dataframe(msg["rows"])

# New question
if question := st.chat_input("Ask about your usage..."):
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Querying..."):
            try:
                result = api_post("/ai/query", {"question": question, "tenant_id": tenant_id})
                st.write(result.get("answer", "No answer returned."))
                if result.get("sql"):
                    with st.expander("View SQL"):
                        st.code(result["sql"], language="sql")
                if result.get("rows"):
                    with st.expander("View raw data"):
                        st.dataframe(result["rows"])
            except Exception as e:
                result = {"answer": f"Error: {e}", "sql": "", "rows": []}
                st.error(result["answer"])

    st.session_state.messages.append({
        "role":    "assistant",
        "content": result.get("answer", ""),
        "sql":     result.get("sql", ""),
        "rows":    result.get("rows", []),
    })

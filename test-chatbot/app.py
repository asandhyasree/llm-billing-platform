"""
Simple test chatbot that routes all LLM calls through the billing proxy.

Instead of calling OpenAI directly, it calls:
  http://localhost:8000/v1/chat/completions

This lets you verify the billing platform is working end-to-end:
  - API key authentication
  - Credit balance checks
  - Token counting and cost calculation
  - Usage event logging
"""
import streamlit as st
import httpx

PROXY_URL = "http://localhost:8000"

st.set_page_config(page_title="Test Chatbot", layout="centered")
st.title("Test Chatbot")
st.caption("All requests go through the billing proxy at localhost:8000")

# Sidebar config
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("API Key", type="password", placeholder="llmbill-...")
    model = st.selectbox("Model", [
        "gpt-4o-mini",
        "gpt-4o",
        "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001",
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
    ])
    st.divider()
    if st.button("Clear chat"):
        st.session_state.messages = []
        st.rerun()

if not api_key:
    st.info("Enter your billing platform API key in the sidebar to start chatting.")
    st.stop()

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Chat input
if prompt := st.chat_input("Say something..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                resp = httpx.post(
                    f"{PROXY_URL}/v1/chat/completions",
                    json={
                        "model": model,
                        "messages": [
                            {"role": m["role"], "content": m["content"]}
                            for m in st.session_state.messages
                        ],
                    },
                    headers={"X-API-Key": api_key},
                    timeout=120,
                )

                if resp.status_code == 402:
                    st.error("Insufficient credits. Top up via the admin dashboard.")
                    st.stop()
                elif resp.status_code == 401:
                    st.error("Invalid API key.")
                    st.stop()
                elif resp.status_code != 200:
                    st.error(f"Error {resp.status_code}: {resp.text}")
                    st.stop()

                data = resp.json()

                # Extract the reply (OpenAI format)
                reply = data["choices"][0]["message"]["content"]
                st.write(reply)

                # Show token usage in an expander
                usage = data.get("usage", {})
                if usage:
                    with st.expander("Token usage"):
                        cols = st.columns(3)
                        cols[0].metric("Input tokens", usage.get("prompt_tokens", usage.get("input_tokens", "?")))
                        cols[1].metric("Output tokens", usage.get("completion_tokens", usage.get("output_tokens", "?")))
                        cols[2].metric("Total tokens", usage.get("total_tokens", "?"))

            except httpx.ConnectError:
                reply = "Could not connect to the billing proxy at localhost:8000. Is the backend running?"
                st.error(reply)
            except Exception as e:
                reply = f"Error: {e}"
                st.error(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

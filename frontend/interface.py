"""Banking AI-Agent — Streamlit Frontend.

A simple chat interface that sends customer messages to the API Gateway
and displays the agent's response along with the workflow trace.
"""

import os

import requests
import streamlit as st

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Banking AI-Agent",
    page_icon="🏦",
    layout="wide",
)

st.title("🏦 Banking AI-Agent")
st.caption("Lab 4 — Microservice Architecture with gRPC & Docker")

# ---------------------------------------------------------------------------
# Sidebar — system info
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("⚙️ System Info")

    # Health check
    try:
        health = requests.get(f"{API_BASE_URL}/health", timeout=5).json()
        st.success(f"API Gateway: **{health.get('status', 'unknown')}**")
    except Exception:
        st.error("API Gateway: **unreachable**")

    # Config
    try:
        config = requests.get(f"{API_BASE_URL}/config", timeout=5).json()
        st.json(config)
    except Exception:
        st.warning("Could not fetch config.")

    st.divider()
    st.caption(f"API URL: `{API_BASE_URL}`")

# ---------------------------------------------------------------------------
# Chat interface
# ---------------------------------------------------------------------------

# Session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "trace" in msg:
            with st.expander("📋 Workflow Trace", expanded=False):
                st.json(msg["trace"])

# Chat input
if prompt := st.chat_input("Type your banking question here..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call API Gateway
    with st.chat_message("assistant"):
        with st.spinner("Processing your request..."):
            try:
                response = requests.post(
                    f"{API_BASE_URL}/run-agent",
                    json={"message": prompt},
                    timeout=300,
                )
                response.raise_for_status()
                data = response.json()

                final_response = data.get("final_response", "No response.")
                decision = data.get("decision", {})
                trace = data.get("trace", {})
                extra = data.get("extra", {})

                # Display the response
                st.markdown(final_response)

                # Decision badge
                action = decision.get("action", "unknown")
                if action == "reply":
                    st.success(f"✅ Action: **{action}** — {decision.get('reason', '')}")
                elif action == "escalate":
                    st.error(f"🚨 Action: **{action}** — {decision.get('reason', '')}")
                elif action == "ask_more":
                    st.warning(f"❓ Action: **{action}** — {decision.get('reason', '')}")

                # Latency
                if "latency_ms" in extra:
                    st.caption(f"⏱️ Latency: {extra['latency_ms']}ms")

                # Trace expander
                with st.expander("📋 Workflow Trace", expanded=False):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("🎯 Intent")
                        st.json(trace.get("intent", {}))

                        st.subheader("⚡ Priority")
                        st.json(trace.get("priority", {}))

                    with col2:
                        st.subheader("📜 Policy")
                        st.json(trace.get("policy", {}))

                        st.subheader("✅ Validation")
                        st.json(trace.get("validation", {}))

                    st.subheader("📝 Draft")
                    st.json(trace.get("draft", {}))

                # Save to history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_response,
                    "trace": data,
                })

            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to API Gateway. Is the backend running?")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "❌ Connection error — backend unreachable.",
                })
            except Exception as exc:
                st.error(f"❌ Error: {exc}")
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ Error: {exc}",
                })

import streamlit as st
import requests
import os
from dotenv import load_dotenv

# ========================= CONFIG =========================
st.set_page_config(
    page_title="FX Agent • Smart Currency Assistant",
    page_icon="💲",
    layout="centered",
    initial_sidebar_state="expanded"
)

load_dotenv()

def get_backend_url():
    try:
        return st.secrets["api"]["BASE_URL"].rstrip("/")
    except Exception:
        return os.getenv("API_URL", "https://fx-agent.onrender.com").rstrip("/")

API_URL = get_backend_url()

# ========================= SESSION STATE =========================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# ========================= HEADER =========================
st.title("💲 FX Agent")
st.markdown("**Autonomous Currency Analysis & Forecasting Assistant**")

# ========================= QUICK ACTION BUTTONS =========================
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("📊 INR → AUD Now", use_container_width=True):
        st.session_state.pending_prompt = "Should I convert INR to AUD now?"
with col2:
    if st.button("💱 Current Rates", use_container_width=True):
        st.session_state.pending_prompt = "What are the current INR to AUD and INR to USD rates?"
with col3:
    if st.button("📈 Run Evaluation", use_container_width=True):
        st.session_state.pending_prompt = "!eval"
with col4:
    if st.button("💰 Cost Summary", use_container_width=True):
        st.session_state.pending_prompt = "cost summary"

# ========================= PROCESS PENDING PROMPT (from buttons) =========================
if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None  # Clear it immediately

    # Add to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Process the prompt with the agent
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing market data & running simulations..."):
            try:
                payload = {
                    "message": prompt,
                    "session_id": st.session_state.session_id
                }

                response = requests.post(
                    f"{API_URL}/chat",
                    json=payload,
                    timeout=90
                )

                if response.status_code == 200:
                    data = response.json()
                    assistant_reply = data.get("response", "No response received.")
                    new_session_id = data.get("session_id")

                    if new_session_id:
                        st.session_state.session_id = new_session_id

                    st.markdown(assistant_reply)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_reply
                    })
                else:
                    error_msg = f"Error {response.status_code}: {response.text[:300]}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

            except Exception as e:
                error_msg = f"❌ Connection error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# ========================= DISPLAY CHAT HISTORY =========================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ========================= NORMAL CHAT INPUT =========================
if prompt := st.chat_input("Ask about exchange rates, forecasts, or conversions..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing market data & running simulations..."):
            try:
                payload = {
                    "message": prompt,
                    "session_id": st.session_state.session_id
                }

                response = requests.post(
                    f"{API_URL}/chat",
                    json=payload,
                    timeout=90
                )

                if response.status_code == 200:
                    data = response.json()
                    assistant_reply = data.get("response", "No response received.")
                    new_session_id = data.get("session_id")

                    if new_session_id:
                        st.session_state.session_id = new_session_id

                    st.markdown(assistant_reply)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_reply
                    })
                else:
                    error_msg = f"Error {response.status_code}: {response.text[:300]}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

            except Exception as e:
                error_msg = f"❌ Connection error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# ========================= FOOTER =========================
st.divider()
st.caption(
    "💲 FX Agent • Monte Carlo Simulations + Technical Analysis • "
    "Session preserved across messages"
)
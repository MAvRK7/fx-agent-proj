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

# ========================= HEADER & QUICK ACTIONS =========================
st.title("💲 FX Agent")
st.markdown("**Autonomous Currency Analysis & Forecasting Assistant**")

# Quick Action Buttons
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("📊 INR → AUD Now", use_container_width=True):
        st.session_state.quick_prompt = "Should I convert INR to AUD now?"
with col2:
    if st.button("💱 Current Rates", use_container_width=True):
        st.session_state.quick_prompt = "What are the current INR to AUD and INR to USD rates?"
with col3:
    if st.button("📈 Run Evaluation", use_container_width=True):
        st.session_state.quick_prompt = "!eval"
with col4:
    if st.button("💰 Cost Summary", use_container_width=True):
        st.session_state.quick_prompt = "cost summary"

# Auto-submit quick prompt if button was clicked
if "quick_prompt" in st.session_state and st.session_state.quick_prompt:
    prompt = st.session_state.quick_prompt
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.quick_prompt = None  # clear it

# ========================= SIDEBAR =========================
with st.sidebar:
    st.info("""
    **Ask anything:**
    - Should I send money from India to Australia?
    - 38 lakh INR in AUD?
    - How is the Indian / Aussie economy?
    - When is the best time to convert in 2026?
    """)
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()

    st.caption("Backend: FastAPI on Render • Gemma + Mistral fallback")

# ========================= DISPLAY CHAT HISTORY =========================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ========================= USER INPUT =========================
if prompt := st.chat_input("Ask about exchange rates, forecasts, or conversions..."):
    user_prompt = prompt
else:
    # Handle quick action buttons
    user_prompt = st.session_state.get("quick_prompt")

if user_prompt:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # Assistant response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing market data & running simulations..."):
            try:
                payload = {
                    "message": user_prompt,
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

            except requests.exceptions.RequestException as e:
                error_msg = f"❌ Cannot connect to backend.\n\n{str(e)}\n\nIs your Render service awake?"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                st.error(f"Unexpected error: {str(e)}")

# ========================= FOOTER =========================
st.divider()
st.caption(
    "💲 FX Agent • Monte Carlo + Technical Analysis • "
    "Session preserved • Deployed on Render + Streamlit"
)
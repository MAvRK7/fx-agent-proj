import streamlit as st
import requests
import os
from dotenv import load_dotenv
from typing import Optional

# ========================= CONFIG =========================
st.set_page_config(
    page_title="FX Agent • Smart Currency Assistant",
    page_icon="💲",
    layout="centered",
    initial_sidebar_state="expanded"
)

load_dotenv()

# Get backend URL - prefer Streamlit secrets, then .env, then default
def get_backend_url():
    try:
        # For deployed Streamlit Cloud
        return st.secrets["api"]["BASE_URL"].rstrip("/")
    except Exception:
        # For local development
        return os.getenv("API_URL", "https://fx-agent.onrender.com").rstrip("/")

API_URL = get_backend_url()

# ========================= SIDEBAR =========================
with st.sidebar:
    st.title("💲 FX Agent")
    st.markdown("### Autonomous Currency Assistant")
    
    st.info("""
    Ask anything about exchange rates and forecasts.

    **Examples:**
    - Should I convert INR to AUD now?
    - Current INR to USD rate?
    - 38 lakh INR in AUD?
    - How is the Indian economy?
    - !eval or cost summary
    """)
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()

    st.caption("Backend: FastAPI on Render • Gemma + Mistral fallback")

# ========================= SESSION STATE =========================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# ========================= DISPLAY CHAT HISTORY =========================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ========================= USER INPUT =========================
if prompt := st.chat_input("Ask about rates, forecasts, or type !eval / cost..."):
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Show thinking spinner
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
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
                    
                    # Save assistant reply
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_reply
                    })

                else:
                    error_msg = f"Error {response.status_code}: {response.text[:200]}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

            except requests.exceptions.RequestException as e:
                error_msg = f"❌ Connection error to backend.\n\n{str(e)}\n\nMake sure your Render backend is awake."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# ========================= FOOTER =========================
st.caption("💲 FX Agent • Session maintained across messages • Powered by Render + Streamlit")
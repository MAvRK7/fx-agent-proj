import streamlit as st
import requests
import json
from typing import Optional

# ========================= CONFIG =========================
st.set_page_config(
    page_title="FX Agent • INR ↔ AUD & More",
    page_icon="💲",
    layout="centered",
    initial_sidebar_state="expanded"
)

API_URL = "https://fx-agent.onrender.com"   # ← Change to your Render URL

# ========================= SIDEBAR =========================
with st.sidebar:
    st.title("💲 FX Agent")
    st.markdown("### Autonomous Currency Assistant")
    
    st.info(
        "Ask anything about exchange rates, forecasts, or conversions.\n\n"
        "Examples:\n"
        "- Should I convert INR to AUD now?\n"
        "- What's the current INR to USD rate?\n"
        "- 38 lakh INR in AUD?\n"
        "- How is the Indian economy?"
    )
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()

    st.caption("Backend: FastAPI on Render • Model: Gemma / Mistral fallback")

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
if prompt := st.chat_input("Ask about currency rates, forecasts, or conversions..."):
    
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Show assistant thinking
    with st.chat_message("assistant"):
        with st.spinner("Analyzing FX data..."):
            try:
                payload = {
                    "message": prompt,
                    "session_id": st.session_state.session_id
                }
                
                response = requests.post(
                    f"{API_URL}/chat",
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    assistant_reply = data.get("response", "Sorry, I couldn't process that.")
                    new_session_id = data.get("session_id")
                    
                    if new_session_id:
                        st.session_state.session_id = new_session_id
                    
                    st.markdown(assistant_reply)
                    
                    # Save to history
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": assistant_reply
                    })
                    
                else:
                    error_msg = f"Error {response.status_code}: {response.text}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"Connection error: {str(e)}\n\nMake sure the backend is running."
                st.error(error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})

# ========================= FOOTER =========================
st.caption("Powered by your FX Agent • Session preserved across messages")
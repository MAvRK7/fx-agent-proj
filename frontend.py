import streamlit as st
import requests
import os
from dotenv import load_dotenv
import time
import threading

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
if "keep_awake" not in st.session_state:
    st.session_state.keep_awake = False   # Default: OFF
if "last_ping" not in st.session_state:
    st.session_state.last_ping = None

# Background ping function
def keep_backend_awake():
    while st.session_state.keep_awake:
        try:
            requests.get(f"{API_URL}/health", timeout=10)
            st.session_state.last_ping = time.strftime("%H:%M:%S")
        except:
            pass  # Silent fail - don't disturb user
        time.sleep(240)  # Ping every 4 minutes (Render sleeps after ~15 min)

# Start background thread if toggle is ON
if st.session_state.keep_awake and "awake_thread" not in st.session_state:
    thread = threading.Thread(target=keep_backend_awake, daemon=True)
    thread.start()
    st.session_state.awake_thread = thread

# ========================= HEADER =========================
st.title("💲 FX Agent")
st.markdown("**Autonomous Currency Analysis & Forecasting Assistant**")

# Keep Awake Toggle
col_toggle, col_status = st.columns([3, 2])
with col_toggle:
    keep_awake = st.toggle(
        "🔄 Keep Backend Awake (prevent 502 errors)",
        value=st.session_state.keep_awake,
        help="When ON, the app will ping the Render backend every 4 minutes to stop it from sleeping."
    )

# Update state if toggle changed
if keep_awake != st.session_state.keep_awake:
    st.session_state.keep_awake = keep_awake
    st.rerun()  # Restart to apply thread change

with col_status:
    if st.session_state.keep_awake:
        st.success("🟢 Awake mode ON")
        if st.session_state.last_ping:
            st.caption(f"Last ping: {st.session_state.last_ping}")
    else:
        st.warning("⚪ Awake mode OFF")

# ========================= QUICK ACTION BUTTONS =========================
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("📊 INR → AUD Now", use_container_width=True, key="btn_inr_aud"):
        st.session_state.pending_prompt = "Should I convert INR to AUD now?"
with col2:
    if st.button("💱 Current Rates", use_container_width=True, key="btn_rates"):
        st.session_state.pending_prompt = "What are the current INR to AUD and INR to USD rates?"
with col3:
    if st.button("📈 Run Evaluation", use_container_width=True, key="btn_eval"):
        st.session_state.pending_prompt = "!eval"
with col4:
    if st.button("💰 Cost Summary", use_container_width=True, key="btn_cost"):
        st.session_state.pending_prompt = "cost summary"

# ========================= SIDEBAR =========================
with st.sidebar:
    st.info("""
    **Try these examples:**
    - Should I convert INR to AUD now?
    - What's the current rate?
    - 38 lakh INR in AUD?
    - How is the Indian economy?
    - When is the best time in 2026?
    
    **Special commands:**
    - `cost summary`
    - `!eval`
    """)
    
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()

    st.caption("Backend: FastAPI on Render\nModel: Gemma + Mistral fallback")

# ========================= PROCESS PENDING PROMPT (Buttons) =========================
if "pending_prompt" in st.session_state and st.session_state.pending_prompt:
    prompt = st.session_state.pending_prompt
    st.session_state.pending_prompt = None

    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Waking up backend & analyzing..."):
        try:
            payload = {"message": prompt, "session_id": st.session_state.session_id}
                
            response = requests.post(f"{API_URL}/chat", json=payload, timeout=120)

            if response.status_code == 200:
                data = response.json()
                assistant_reply = data.get("response", "No response")
                if data.get("session_id"):
                    st.session_state.session_id = data["session_id"]

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_reply
                })
                st.rerun()
            else:
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"Error {response.status_code}"
                })
        
                    
        except requests.exceptions.RequestException:
            st.error("⚠️ Backend is sleeping (502). Please wait 10–20 seconds and try again.")
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "⚠️ The backend is waking up from sleep. Please try again in 15 seconds."
            })

# ========================= DISPLAY CHAT HISTORY =========================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ========================= NORMAL CHAT INPUT =========================
if prompt := st.chat_input("Ask about exchange rates, forecasts, or conversions..."):
    st.session_state.messages.append({"role": "user", "content": prompt})

   
    with st.spinner("Analyzing market data & running simulations..."):
        try:
            payload = {"message": prompt, "session_id": st.session_state.session_id}
            response = requests.post(f"{API_URL}/chat", json=payload, timeout=120)

            if response.status_code == 200:
                data = response.json()
                assistant_reply = data.get("response", "No response received.")
                if data.get("session_id"):
                    st.session_state.session_id = data["session_id"]
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_reply
                })
                st.rerun()
            else:
                st.error(f"Backend returned error {response.status_code}")
        except requests.exceptions.RequestException:
            st.error("⚠️ Backend is sleeping. Wait 10–20 seconds and try again.")
            st.session_state.messages.append({
                "role": "assistant", 
                "content": "The backend is waking up. Please wait a moment and try again."
            })

# ========================= FOOTER =========================
st.divider()
st.caption("💲 FX Agent • Monte Carlo + Technical Analysis • Render + Streamlit")
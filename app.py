import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- 1. SETUP & SECRETS ---
# Store your key in GitHub/Streamlit under: Settings -> Secrets
# Name: GEMINI_API_KEY | Value: your_key_here
API_KEY = st.secrets.get("GEMINI_API_KEY", "")

st.set_page_config(page_title="Sensei Stefan v5", layout="wide")

# --- 2. RADIKALES iPAD DESIGN ---
st.markdown(f"""
    <style>
    /* Background & Body */
    .stApp {{ background: #0e1117; }}
    
    /* Stefan's Text (Your Input) - Made Smaller */
    .user-text {{ font-size: 1.0rem !important; color: #888; font-style: italic; }}
    
    /* Seller Text - Visible Later */
    .sensei-text {{ font-size: 1.8rem !important; font-weight: bold; color: #ff4b4b; line-height: 1.4; }}

    /* Microphone Button Centering & Size */
    div[data-testid="stVerticalBlock"] > div:has(svg) {{
        display: flex; justify-content: center; transform: scale(2.5); margin: 60px 0;
    }}
    
    /* Buttons optimized for Touch (iPad) */
    .stButton > button {{
        width: 100%; height: 70px; font-size: 1.4rem !important; border-radius: 15px;
    }}
    </style>
""", unsafe_allow_html=True)

# --- 3. LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_text" not in st.session_state:
    st.session_state.show_text = False

def get_ai_response(audio_bytes, situation):
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
    prompt = f"You are a seller at {situation}. Stefan (math teacher) is speaking. Answer cheekily/politely. FORMAT: JAPANESE: [Text] GERMAN: [Text]"
    response = model.generate_content([prompt, audio_part])
    return response.text

# --- 4. UI ---
st.title("🇯🇵 Sensei Stefan: Listening Training")

with st.sidebar:
    situation = st.selectbox("Location:", ["Takezono Butcher Shop", "McDonald's Ashiya", "Bus to Arima Onsen"])
    if st.button("Reset"):
        st.session_state.messages = []
        st.rerun()

# THE MICROPHONE (Central & Large)
st.write("### 🎤 Press and speak (Stops after 5s of silence):")
audio_data = audio_recorder(
    text="",
    recording_color="#ff4b4b",
    neutral_color="#666",
    pause_threshold=5.0, # <--- Here: Tolerates 5 seconds of silence!
    key="mic"
)

if audio_data and not st.session_state.get("processing", False):
    st.session_state.processing = True
    with st.spinner("The seller is thinking..."):
        answer = get_ai_response(audio_data, situation)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.show_text = False # Hide text with new answer
        st.session_state.processing = False
        st.rerun()

# CHAT HISTORY
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        # 1. PLAY AUDIO IMMEDIATELY
        jp_text = msg["content"].split("JAPANESE:")[1].split("GERMAN:")[0].strip()
        tts = gTTS(text=jp_text, lang='ja')
        b = io.BytesIO()
        tts.write_to_fp(b)
        b64 = base64.b64encode(b.getvalue()).decode()
        st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" autoplay controls></audio>', unsafe_allow_html=True)
        
        # 2. SHOW TEXT OPTIONALLY
        if st.button("👁️ Read the seller's answer?", key=msg["content"][:20]):
            st.session_state.show_text = True
        
        if st.session_state.show_text:
            st.markdown(f'<p class="sensei-text">{msg["content"]}</p>', unsafe_allow_html=True)
    else:
        st.markdown(f'<p class="user-text">Stefan: {msg["content"]}</p>', unsafe_allow_html=True)

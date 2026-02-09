import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- API SETUP ---
API_KEY = st.secrets.get("GEMINI_API_KEY")

# --- DESIGN SETUP ---
st.set_page_config(page_title="Japan Trainer v12", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .main .block-container { max-width: 850px; padding: 1.5rem; margin: auto; }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] { padding: 20px 10px; background-color: #161b22; }
    section[data-testid="stSidebar"] .stMarkdown p, section[data-testid="stSidebar"] label {
        font-size: 0.8rem !important; color: #aaa !important; margin-left: 10px;
    }

    /* Text-Boxen */
    .stefan-box { font-size: 0.9rem; color: #888; font-style: italic; margin-bottom: 10px; }
    .seller-box { 
        font-size: 1.3rem !important; color: #00ffcc; background: #1a1c23; 
        padding: 18px; border-radius: 10px; border-left: 4px solid #ff4b4b;
    }

    /* Mikrofon */
    div[data-testid="stVerticalBlock"] > div:has(svg) {
        display: flex; justify-content: center; transform: scale(2.0); margin: 30px 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- MODEL FINDER ---
@st.cache_resource
def get_working_model(api_key):
    try:
        genai.configure(api_key=api_key)
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for target in ['models/gemini-1.5-flash', 'models/gemini-pro']:
            if target in available: return genai.GenerativeModel(target)
        return genai.GenerativeModel(available[0]) if available else None
    except: return None

# --- LOGIK ---
if "chat" not in st.session_state: st.session_state.chat = []
if "last_audio_hash" not in st.session_state: st.session_state.last_audio_hash = None

def talk_to_seller(audio_bytes, sit):
    model = get_working_model(API_KEY)
    if not model: return "API Fehler"
    try:
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        prompt = (f"Du bist eine höfliche Verkäuferin in {sit} (Kansai-Region). "
                  "Stefan (Mathelehrer) spricht per Audio zu dir. "
                  "1. Transkribiere zuerst kurz, was Stefan gesagt hat (auf Deutsch/Japanisch). "
                  "2. Antworte höflich, aber mit einem charmanten Kansai-Dialekt (Kansai-ben). "
                  "FORMAT IMMER EXAKT SO:\n"
                  "STEFAN: [Was du verstanden hast]\n"
                  "JAPANISCH: [Deine Antwort]\n"
                  "DEUTSCH: [Übersetzung]")
        res = model.generate_content([prompt, audio_part])
        return res.text
    except Exception as e: return f"API Fehler: {str(e)}"

# --- UI ---
st.title("🇯🇵 Sensei Stefan: Kansai Edition")

with st.sidebar:
    st.markdown("### 📍 Location")
    situation = st.selectbox("Ort:", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus Arima Onsen"], key="sit_v12")
    if st.button("Gespräch zurücksetzen"):
        st.session_state.chat = []
        st.session_state.last_audio_hash = None
        st.rerun()

st.write(f"Du bist gerade in: **{situation}**")

# Mikrofon
audio_data = audio_recorder(text="", pause_threshold=4.0, key="mic_v12")

if audio_data is not None:
    curr_hash = hash(audio_data)
    if st.session_state.last_audio_hash != curr_hash:
        st.session_state.last_audio_hash = curr_hash
        with st.spinner("Höre zu..."):
            answer = talk_to_seller(audio_data, situation)
            st.session_state.chat.append(answer)

# Chat Verlauf
for msg in reversed(st.session_state.chat):
    st.divider()
    
    # Trennung der KI-Antwort
    parts = {"stefan": "", "japanisch": "", "full": msg}
    if "STEFAN:" in msg and "JAPANISCH:" in msg:
        parts["stefan"] = msg.split("STEFAN:")[1].split("JAPANISCH:")[0].strip()
        parts["japanisch"] = msg.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip()

    # 1. Was Stefan gesagt hat (Dezent anzeigen)
    if parts["stefan"]:
        st.markdown(f'<p class="stefan-box">Verstanden: "{parts["stefan"]}"</p>', unsafe_allow_html=True)

    # 2. Audio der Verkäuferin
    if parts["japanisch"]:
        try:
            tts = gTTS(text=parts["japanisch"], lang='ja')
            b = io.BytesIO(); tts.write_to_fp(b)
            b64 = base64.b64encode(b.getvalue()).decode()
            st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls autoplay></audio>', unsafe_allow_html=True)
        except: pass

    # 3. Antwort-Text hinter Expander
    with st.expander("👁️ Antwort der Verkäuferin (Kansai-ben)"):
        st.markdown(f'<div class="seller-box">{msg}</div>', unsafe_allow_html=True)

st.divider()

import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- API SETUP ---
API_KEY = st.secrets.get("GEMINI_API_KEY")

# --- iPAD DESIGN FIX v11 ---
st.set_page_config(page_title="Japan Trainer", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    
    /* Hauptbereich */
    .main .block-container {
        max-width: 850px !important;
        padding: 1.5rem !important;
        margin: auto;
    }

    /* SIDEBAR: Kleiner und eingerückt */
    section[data-testid="stSidebar"] {
        padding: 20px 10px !important;
        background-color: #161b22 !important;
    }
    
    /* Sidebar Text & Labels verkleinern */
    section[data-testid="stSidebar"] .stMarkdown p, 
    section[data-testid="stSidebar"] label {
        font-size: 0.85rem !important;
        color: #aaa !important;
        margin-left: 10px;
    }

    /* Selectbox und Button in der Sidebar schrumpfen */
    section[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] {
        font-size: 0.8rem !important;
        transform: scale(0.95);
        margin-left: 5px;
    }
    
    section[data-testid="stSidebar"] .stButton button {
        font-size: 0.75rem !important;
        height: 35px !important;
        margin-left: 10px;
    }

    /* Antwort-Box der Verkäuferin */
    .seller-box { 
        font-size: 1.3rem !important; 
        color: #00ffcc; 
        background: #1a1c23; 
        padding: 18px; 
        border-radius: 10px; 
    }

    /* Mikrofon */
    div[data-testid="stVerticalBlock"] > div:has(svg) {
        display: flex; justify-content: center; transform: scale(2.0); margin: 30px 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- MODELL FINDER ---
@st.cache_resource
def get_working_model(api_key):
    try:
        genai.configure(api_key=api_key)
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for target in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if target in available: return genai.GenerativeModel(target)
        return genai.GenerativeModel(available[0]) if available else None
    except: return None

# --- LOGIK ---
if "chat" not in st.session_state: st.session_state.chat = []
if "last_audio_hash" not in st.session_state: st.session_state.last_audio_hash = None

def talk_to_seller(audio_bytes, sit):
    model = get_working_model(API_KEY)
    if not model: return "API Fehler: Kein Modell gefunden."
    try:
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        prompt = (f"Du bist Verkäuferin bei {sit}. Antworte kurz und frech auf Japanisch. "
                  "FORMAT: JAPANISCH: [Satz] DEUTSCH: [Übersetzung]")
        res = model.generate_content([prompt, audio_part])
        return res.text
    except Exception as e: return f"API Fehler: {str(e)}"

# --- UI ---
st.title("🇯🇵 Sensei Stefan")

with st.sidebar:
    st.markdown("### 📍 Menü")
    situation = st.selectbox("Ort wählen:", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus Arima Onsen"], key="sit_v11")
    st.markdown("---")
    if st.button("Chat löschen"):
        st.session_state.chat = []
        st.session_state.last_audio_hash = None
        st.rerun()

st.write(f"Ort: **{situation}**")

# Mikrofon
audio_data = audio_recorder(text="", pause_threshold=4.0, key="mic_v11")

if audio_data is not None:
    curr_hash = hash(audio_data)
    if st.session_state.last_audio_hash != curr_hash:
        st.session_state.last_audio_hash = curr_hash
        with st.spinner("..."):
            answer = talk_to_seller(audio_data, situation)
            st.session_state.chat.append(answer)

# Chat Verlauf
for msg in reversed(st.session_state.chat):
    st.divider()
    try:
        jp = msg.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip() if "JAPANISCH:" in msg else msg
        tts = gTTS(text=jp, lang='ja')
        b = io.BytesIO(); tts.write_to_fp(b)
        b64 = base64.b64encode(b.getvalue()).decode()
        st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls autoplay></audio>', unsafe_allow_html=True)
    except: pass

    with st.expander("👁️ Antwort lesen"):
        st.markdown(f'<div class="seller-box">{msg}</div>', unsafe_allow_html=True)

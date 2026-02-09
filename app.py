import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- API SETUP ---
API_KEY = st.secrets.get("GEMINI_API_KEY")

# --- iPAD OPTIMIERTES DESIGN ---
st.set_page_config(page_title="Japan Trainer", layout="wide")

st.markdown("""
    <style>
    /* Hintergrund */
    .stApp { background-color: #0e1117; }
    
    /* Hauptinhalt: Mehr Platz zu den Rändern */
    .main .block-container {
        max-width: 95% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        margin: auto;
    }

    /* SIDEBAR FIX: Verhindert, dass Text am Kante klebt */
    section[data-testid="stSidebar"] {
        padding: 20px 10px !important;
        min-width: 300px !important;
    }
    
    /* Text in der Sidebar einrücken */
    section[data-testid="stSidebar"] .stSelectbox, 
    section[data-testid="stSidebar"] .stButton {
        padding: 0 10px !important;
    }

    /* Antwort-Box der Verkäuferin */
    .seller-box { 
        font-size: 1.3rem !important; 
        color: #00ffcc; 
        background: #1a1c23; 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #333;
        word-wrap: break-word;
    }

    /* Mikrofon-Zentrierung */
    div[data-testid="stVerticalBlock"] > div:has(svg) {
        display: flex; justify-content: center; transform: scale(2.2); margin: 30px 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- MODEL-LOGIK (FIX FÜR 404 FEHLER) ---
@st.cache_resource
def get_model(api_key):
    try:
        genai.configure(api_key=api_key)
        # Wir versuchen die stabilste Version des Namens
        return genai.GenerativeModel('gemini-1.5-flash-latest')
    except:
        # Fallback falls 'latest' nicht geht
        return genai.GenerativeModel('gemini-pro')

# --- LOGIK ---
if "chat" not in st.session_state:
    st.session_state.chat = []
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

def talk_to_seller(audio_bytes, sit):
    if not API_KEY:
        return "Fehler: Kein API Key gefunden."
    try:
        model = get_model(API_KEY)
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        prompt = (f"Du bist Verkäuferin bei {sit}. Stefan ist Mathelehrer. "
                  "Antworte kurz und höflich-frech. "
                  "FORMAT: JAPANISCH: [Satz] DEUTSCH: [Übersetzung]")
        res = model.generate_content([prompt, audio_part])
        return res.text
    except Exception as e:
        return f"System-Fehler: {str(e)}"

# --- UI ---
st.title("🇯🇵 Sensei Stefan")

# Sidebar (Mit Abständen fixiert)
with st.sidebar:
    st.markdown("### 📍 Training")
    situation = st.selectbox(
        "Wo bist du?", 
        ["Metzgerei Takezono", "McDonald's Ashiya", "Bus Arima Onsen"],
        key="location_select"
    )
    st.divider()
    if st.button("Chat löschen", use_container_width=True):
        st.session_state.chat = []
        st.session_state.last_audio = None
        st.rerun()

st.write(f"Du bist hier: **{situation}**")

# Mikrofon
audio_data = audio_recorder(text="", pause_threshold=4.0, key="mic_v9")

if audio_data is not None and audio_data != st.session_state.last_audio:
    st.session_state.last_audio = audio_data
    with st.spinner("Höre zu..."):
        answer = talk_to_seller(audio_data, situation)
        st.session_state.chat.append(answer)

# Nachrichtenanzeige
for msg in reversed(st.session_state.chat):
    st.divider()
    
    # Audio Logik
    try:
        if "JAPANISCH:" in msg:
            jp = msg.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip()
        else:
            jp = msg
        
        tts = gTTS(text=jp, lang='ja')
        b = io.BytesIO()
        tts.write_to_fp(b)
        b64 = base64.b64encode(b.getvalue()).decode()
        st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls autoplay></audio>', unsafe_allow_html=True)
    except:
        st.info("🔈 Audio wird erstellt...")

    with st.expander("👁️ Antwort lesen"):
        st.markdown(f'<div class="seller-box">{msg}</div>', unsafe_allow_html=True)

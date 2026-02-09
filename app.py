import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- API SETUP ---
API_KEY = st.secrets.get("GEMINI_API_KEY")

# --- DESIGN: SCHMALER BODY & GROSSE SCHRIFT ---
st.set_page_config(page_title="Sensei Stefan", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    
    /* Begrenzt die Breite auf dem iPad, damit es nicht "aufgebläht" wirkt */
    .block-container {
        max-width: 700px !important;
        padding-top: 2rem !important;
        margin: auto;
    }

    /* Stefan's Text: Dezent */
    .user-box { font-size: 0.8rem !important; color: #888; text-align: center; }
    
    /* Verkäuferin: Fokus auf Lesbarkeit */
    .seller-box { 
        font-size: 1.5rem !important; 
        color: #00ffcc; 
        background: #1a1c23; 
        padding: 20px; 
        border-radius: 12px; 
        border: 1px solid #333;
        line-height: 1.4;
    }

    /* Mikrofon: Riesig und zentriert */
    div[data-testid="stVerticalBlock"] > div:has(svg) {
        display: flex; justify-content: center; transform: scale(3.5); margin: 60px 0;
    }
    
    /* Audio Player Breite anpassen */
    audio { width: 100%; }
    </style>
""", unsafe_allow_html=True)

if not API_KEY:
    st.error("❌ API Key fehlt in den Streamlit Secrets!")
    st.stop()

# --- LOGIK ---
if "chat" not in st.session_state: 
    st.session_state.chat = []

def talk_to_seller(audio_bytes, sit):
    try:
        genai.configure(api_key=API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        prompt = (f"Du bist Verkäuferin bei {sit}. Stefan (Mathelehrer) spricht zu dir. "
                  "Antworte kurz, höflich und etwas frech. "
                  "FORMAT: JAPANISCH: [Satz] DEUTSCH: [Übersetzung]")
        
        res = model.generate_content([prompt, audio_part])
        return res.text
    except Exception as e:
        return f"Fehler: {str(e)}"

# --- UI ---
st.title("🇯🇵 Sensei Stefan")

with st.sidebar:
    sit = st.selectbox("Ort:", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus Arima Onsen"])
    if st.button("Verlauf löschen"):
        st.session_state.chat = []
        st.rerun()

# Mikrofon
audio_data = audio_recorder(
    text="", 
    recording_color="#e74c3c", 
    neutral_color="#95a5a6",
    pause_threshold=5.0
)

# Verarbeitung (Abbruch bei Fehlern verhindern)
if audio_data is not None:
    # Verhindert doppeltes Senden des gleichen Audio-Schnippsels
    if "last_processed" not in st.session_state or st.session_state.last_processed != hash(audio_data):
        with st.spinner("Verkäuferin hört zu..."):
            answer = talk_to_seller(audio_data, sit)
            st.session_state.chat.append(answer)
            st.session_state.last_processed = hash(audio_data)

# Chat-Anzeige (Neueste Nachricht oben)
for msg in reversed(st.session_state.chat):
    st.markdown('<p class="user-box">Stefan hat gesprochen...</p>', unsafe_allow_html=True)
    
    # Audio-Logik
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
        st.warning("Audio konnte nicht geladen werden.")
    
    # Text hinter Expander verstecken für besseres Lernen
    with st.expander("👁️ Antwort lesen"):
        st.markdown(f'<div class="seller-box">{msg}</div>', unsafe_allow_html=True)
    st.divider()

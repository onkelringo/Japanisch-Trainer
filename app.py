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
    /* Hintergrund & Grundschrift */
    .stApp { background-color: #0e1117; }
    
    /* Verhindert, dass Text links/rechts abgeschnitten wird */
    .main .block-container {
        max-width: 90% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        margin: auto;
    }

    /* Antwort-Box der Verkäuferin */
    .seller-box { 
        font-size: 1.3rem !important; 
        color: #00ffcc; 
        background: #1a1c23; 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #333;
        word-wrap: break-word; /* Verhindert Überlaufen */
    }

    /* Stefan's Info-Text */
    .user-info { font-size: 0.8rem; color: #777; margin-bottom: 5px; }

    /* Mikrofon-Zentrierung */
    div[data-testid="stVerticalBlock"] > div:has(svg) {
        display: flex; justify-content: center; transform: scale(2.5); margin: 40px 0;
    }
    
    /* Sidebar Fix für mobile Geräte */
    [data-testid="stSidebar"] { min-width: 250px !important; }
    </style>
""", unsafe_allow_html=True)

# --- MODEL-LOGIK (FIX FÜR 404 FEHLER) ---
def get_model():
    genai.configure(api_key=API_KEY)
    # Probiere flash ohne Pfad oder das Standard-Pro Modell
    return genai.GenerativeModel('gemini-1.5-flash')

# --- LOGIK ---
if "chat" not in st.session_state:
    st.session_state.chat = []
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

def talk_to_seller(audio_bytes, sit):
    try:
        model = get_model()
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        prompt = (f"Du bist Verkäuferin bei {sit}. Stefan ist Mathelehrer. "
                  "Antworte kurz und höflich-frech. "
                  "FORMAT: JAPANISCH: [Satz] DEUTSCH: [Übersetzung]")
        res = model.generate_content([prompt, audio_part])
        return res.text
    except Exception as e:
        return f"Fehler: {str(e)}"

# --- UI ---
st.title("🇯🇵 Sensei Stefan")

# Sidebar für Orte (jetzt stabil)
with st.sidebar:
    st.header("Einstellungen")
    sit = st.selectbox("Wo bist du?", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus Arima Onsen"])
    if st.button("Chat löschen"):
        st.session_state.chat = []
        st.session_state.last_audio = None
        st.rerun()

st.write(f"📍 Aktueller Ort: **{sit}**")

# Mikrofon
audio_data = audio_recorder(text="", pause_threshold=4.0, key="mic_v8")

if audio_data is not None and audio_data != st.session_state.last_audio:
    st.session_state.last_audio = audio_data
    with st.spinner("Höre zu..."):
        answer = talk_to_seller(audio_data, sit)
        st.session_state.chat.append(answer)

# Nachrichten
for msg in reversed(st.session_state.chat):
    st.divider()
    st.markdown('<p class="user-info">Stefan hat gesprochen...</p>', unsafe_allow_html=True)
    
    # Audio Player
    try:
        jp = msg.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip() if "JAPANISCH:" in msg else msg
        tts = gTTS(text=jp, lang='ja')
        b = io.BytesIO()
        tts.write_to_fp(b)
        b64 = base64.b64encode(b.getvalue()).decode()
        st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls autoplay></audio>', unsafe_allow_html=True)
    except:
        st.write("🔈 Audio-Vorschau nicht verfügbar.")

    with st.expander("👁️ Antwort lesen"):
        st.markdown(f'<div class="seller-box">{msg}</div>', unsafe_allow_html=True)

import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- 1. APP INITIALISIERUNG ---
st.set_page_config(page_title="Onkel Ringos Lernapp", layout="wide")

# --- 2. DESIGN (ROT/WEISS/SCHWARZ) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; color: #000000 !important; }
    .main .block-container { max-width: 750px !important; padding: 1.5rem; margin: auto; }
    h1 { color: #bc002d !important; font-weight: 800; border-bottom: 3px solid #bc002d; }
    .seller-box { 
        font-size: 1.4rem !important; color: #ffffff !important; background: #000000 !important; 
        padding: 20px !important; border-radius: 8px !important; border-left: 12px solid #bc002d !important;
    }
    .stefan-info { font-size: 0.9rem !important; color: #555 !important; margin-top: 15px; }
    div[data-testid="stVerticalBlock"] > div:has(svg) {
        display: flex; justify-content: center; transform: scale(2.5); margin: 50px 0;
    }
    svg { fill: #bc002d !important; }
    section[data-testid="stSidebar"] { background-color: #f8f9fa !important; border-right: 1px solid #eee; }
    p, span, label { color: #000000 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. KI LOGIK (ECHTES ROLLENSPIEL) ---
API_KEY = st.secrets.get("GEMINI_API_KEY")

@st.cache_resource
def load_ringo_model(key):
    if not key: return None
    genai.configure(api_key=key)
    return genai.GenerativeModel('gemini-1.5-flash-8b')

if "chat" not in st.session_state: st.session_state.chat = []
if "last_audio_id" not in st.session_state: st.session_state.last_audio_id = None

def get_ai_response(audio_bytes, location):
    model = load_ringo_model(API_KEY)
    if not model: return "Fehler: Key fehlt!"
    try:
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        # Der Prompt zwingt die KI in ein aktives Gespräch
        prompt = (f"Du bist eine echte japanische Verkäuferin in {location}. Stefan ist dein Kunde. "
                  "Verhalte dich wie in einer echten Verkaufssituation: Begrüße ihn, reagiere auf seine Wünsche "
                  "und stelle IMMER eine Anschlussfrage (z.B. 'Wie viel Gramm?', 'Noch etwas dazu?', 'Haben Sie eine Kundenkarte?'). "
                  "Halte das Gespräch lebendig. Falls er einen Fehler macht, korrigiere ihn ganz kurz am Ende auf Deutsch."
                  "\nFORMAT:\nSTEFAN: [Was er sagte]\nJAPANISCH: [Deine Antwort + Frage]\nDEUTSCH: [Übersetzung]")
        
        # Sende minimalen Kontext für flüssigeres Gespräch
        context = st.session_state.chat[-1:] if st.session_state.chat else []
        res = model.generate_content([prompt, *context, audio_part])
        return res.text
    except Exception as e:
        return f"Bitte kurz warten (Limit). Fehler: {str(e)}"

# --- 4. UI ---
st.title("🏯 Onkel Ringos Lernapp")

with st.sidebar:
    st.markdown("### 📍 Umgebung")
    ort = st.selectbox("Wo bist du?", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus Arima Onsen"])
    if st.button("Gespräch neu starten"):
        st.session_state.chat = []
        st.session_state.last_audio_id = None
        st.rerun()

# Verlauf (Neu unten)
for i, msg in enumerate(st.session_state.chat):
    st.divider()
    parts = {"stefan": "", "japan": ""}
    if "STEFAN:" in msg and "JAPANISCH:" in msg:
        parts["stefan"] = msg.split("STEFAN:").split("JAPANISCH:").strip()
        parts["japan"] = msg.split("JAPANISCH:").split("DEUTSCH:").strip()
    else:
        parts["japan"] = msg

    if parts["stefan"]:
        st.markdown(f'<div class="stefan-info">Verstanden: "{parts["stefan"]}"</div>', unsafe_allow_html=True)

    if parts["japan"]:
        try:
            tts = gTTS(text=parts["japan"], lang='ja')
            audio_stream = io.BytesIO()
            tts.write_to_fp(audio_stream)
            b64 = base64.b64encode(audio_stream.getvalue()).decode()
            auto = "autoplay" if i == len(st.session_state.chat)-1 else ""
            st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls {auto}></audio>', unsafe_allow_html=True)
        except: pass

    with st.expander("👁️ Text & Übersetzung anzeigen"):
        st.markdown(f'<div class="seller-box">{msg}</div>', unsafe_allow_html=True)

# Mikrofon
st.write("---")
st.write("### 🎤 Deine Antwort:")
recorded_audio = audio_recorder(text="", icon_size="3x", pause_threshold=3.0, key="ringo_v23_final")

if recorded_audio and recorded_audio != st.session_state.last_audio_id:
    st.session_state.last_audio_id = recorded_audio
    with st.spinner("Die Verkäuferin antwortet..."):
        ai_msg = get_ai_response(recorded_audio, ort)
        st.session_state.chat.append(ai_msg)
        st.rerun()

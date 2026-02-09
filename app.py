import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- 1. KOMPLETTE NEU-INITIALISIERUNG GEGEN CACHING ---
st.set_page_config(page_title="Onkel Ringos Lernapp", layout="wide")

st.markdown("""
    <style>
    /* Radikales Rot-Weiss-Schwarz Design */
    .stApp { background-color: #ffffff !important; }
    .main .block-container { max-width: 700px !important; margin: auto; }
    
    /* Titel */
    h1 { color: #bc002d !important; border-bottom: 4px solid #bc002d !important; }

    /* Antwortbox der Verkäuferin (Schwarz) */
    .ringo-response-box { 
        font-size: 1.4rem !important; color: #ffffff !important; 
        background-color: #000000 !important; padding: 25px !important; 
        border-radius: 5px !important; border-left: 15px solid #bc002d !important;
    }

    /* Deine transkribierten Sätze */
    .user-transcript { font-size: 0.9rem !important; color: #555555 !important; font-style: italic; }

    /* Das Mikrofon (Japan-Rot) */
    div[data-testid="stVerticalBlock"] > div:has(svg) {
        display: flex !important; justify-content: center !important; 
        transform: scale(2.5); margin: 60px 0 !important;
    }
    svg { fill: #bc002d !important; }

    /* Sidebar Clean-up */
    section[data-testid="stSidebar"] { background-color: #f0f2f6 !important; border-right: 2px solid #bc002d; }
    p, span, label { color: #000000 !important; }
    </style>
""", unsafe_allow_html=True)

# --- 2. INTELLIGENTE KI LOGIK ---
def initialize_ringo_ai():
    key = st.secrets.get("GEMINI_API_KEY")
    if not key:
        st.error("API Key fehlt in den Secrets!")
        st.stop()
    genai.configure(api_key=key)
    return genai.GenerativeModel('gemini-1.5-flash-8b')

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_audio_id" not in st.session_state:
    st.session_state.session_audio_id = None

def get_ringo_reply(audio_data, ort):
    model = initialize_ringo_ai()
    try:
        audio_input = {"mime_type": "audio/wav", "data": audio_data}
        prompt = (f"Du bist eine japanische Verkäuferin in {ort}. Stefan ist der Kunde. "
                  "Verhalte dich wie im echten Rollenspiel: Sei höflich, reagiere auf ihn und "
                  "stelle IMMER eine Anschlussfrage, um das Gespräch am Laufen zu halten. "
                  "Falls Stefan einen groben Fehler im Japanischen macht, korrigiere ihn ganz kurz am Ende."
                  "\nFORMAT:\nSTEFAN_SAGTE: [Transkript]\nJAPANISCH: [Antwort + Frage]\nDEUTSCH: [Übersetzung]")
        
        # Nur minimaler Kontext gegen 429-Fehler
        context = st.session_state.chat_history[-1:] if st.session_state.chat_history else []
        response = model.generate_content([prompt, *context, audio_input])
        return response.text
    except Exception as e:
        return f"FEHLER: {str(e)}"

# --- 3. DIE BENUTZEROBERFLÄCHE ---
st.title("🏯 Onkel Ringos Lernapp")

with st.sidebar:
    st.markdown("### 📍 Rollenspiel")
    wahl = st.selectbox("Ort wechseln:", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus Arima Onsen"])
    if st.button("Gespräch neu starten"):
        st.session_state.chat_history = []
        st.session_state.session_audio_id = None
        st.rerun()

# Chat-Verlauf (Neueste Nachricht unten für flüssiges Lesen)
for i, nachricht in enumerate(st.session_state.chat_history):
    st.divider()
    
    # Nachricht zerlegen
    stefan_part = ""
    japan_part = ""
    if "STEFAN_SAGTE:" in nachricht and "JAPANISCH:" in nachricht:
        stefan_part = nachricht.split("STEFAN_SAGTE:")[1].split("JAPANISCH:")[0].strip()
        japan_part = nachricht.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip()
    
    if stefan_part:
        st.markdown(f'<div class="user-transcript">Onkel Ringo verstand: "{stefan_part}"</div>', unsafe_allow_html=True)

    if japan_part:
        try:
            tts = gTTS(text=japan_part, lang='ja')
            audio_io = io.BytesIO()
            tts.write_to_fp(audio_io)
            b64_audio = base64.b64encode(audio_io.getvalue()).decode()
            is_latest = (i == len(st.session_state.chat_history) - 1)
            autoplay = "autoplay" if is_latest else ""
            st.markdown(f'<audio src="data:audio/mp3;base64,{b64_audio}" controls {autoplay}></audio>', unsafe_allow_html=True)
        except: pass

    with st.expander("👁️ Antwort & Übersetzung lesen"):
        st.markdown(f'<div class="ringo-response-box">{nachricht}</div>', unsafe_allow_html=True)

# --- 4. AUFNAHME-STATION ---
st.write("---")
st.write("### 🎤 Sprich jetzt mit der Verkäuferin:")
audio_bytes = audio_recorder(text="", icon_size="3x", pause_threshold=3.0, key="ringo_v22_mic")

if audio_bytes and audio_bytes != st.session_state.session_audio_id:
    st.session_state.session_audio_id = audio_bytes
    with st.spinner("Onkel Ringo wertet aus..."):
        ai_reply = get_ringo_reply(audio_bytes, wahl)
        st.session_state.chat_history.append(ai_reply)
        st.rerun()

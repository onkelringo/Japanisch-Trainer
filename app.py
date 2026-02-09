import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- 1. APP CONFIG (FORCE REFRESH) ---
st.set_page_config(page_title="Onkel Ringos Lernapp", layout="wide")

# --- 2. MINIMAL DESIGN (ROT-WEISS-SCHWARZ) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    .main .block-container { max-width: 700px !important; margin: auto; }
    h1 { color: #bc002d !important; border-bottom: 4px solid #bc002d !important; }
    
    /* Box der Verkäuferin */
    .ringo-response { 
        font-size: 1.4rem !important; color: #ffffff !important; background: #000000 !important; 
        padding: 20px !important; border-left: 15px solid #bc002d !important;
    }
    
    /* Deine Transkription */
    .transcript-style { font-size: 0.9rem !important; color: #666 !important; margin-bottom: 5px; }

    /* Mikrofon (Groß & Rot) */
    div[data-testid="stVerticalBlock"] > div:has(svg) {
        display: flex; justify-content: center; transform: scale(2.8); margin: 50px 0;
    }
    svg { fill: #bc002d !important; }
    
    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #f8f9fa !important; border-right: 1px solid #eee; }
    </style>
""", unsafe_allow_html=True)

# --- 3. DYNAMISCHE MODELL-AUSWAHL (VERHINDERT 404) ---
API_KEY = st.secrets.get("GEMINI_API_KEY")

@st.cache_resource
def get_best_available_model(key):
    if not key: return None
    genai.configure(api_key=key)
    try:
        # Wir fragen Google: Welche Modelle darf dieser Key benutzen?
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Wir suchen unsere Favoriten in dieser Liste
        for model_candidate in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if model_candidate in available_models:
                return genai.GenerativeModel(model_candidate)
        
        # Falls gar nichts passt, nimm das erste verfügbare
        return genai.GenerativeModel(available_models[0]) if available_models else None
    except:
        return None

# --- 4. SESSION STATE ---
if "ringo_messages" not in st.session_state:
    st.session_state.ringo_messages = []
if "last_rec_id" not in st.session_state:
    st.session_state.last_rec_id = None

def process_interaction(audio_bytes, location):
    model = get_best_available_model(API_KEY)
    if not model: return "Fehler: Kein Modell verfügbar. Key prüfen!"
    try:
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        prompt = (f"Du bist eine japanische Verkäuferin in {location}. Stefan ist dein Kunde. "
                  "Führe ein echtes Rollenspiel: Antworte höflich und stelle IMMER eine Gegenfrage "
                  "(Menge, Tüte, Bezahlung, etc.). "
                  "FORMAT: STEFAN: [Transkript] JAPANISCH: [Antwort + Frage] DEUTSCH: [Übersetzung]")
        
        # Nur die letzte Nachricht als Kontext senden (Quota-Schutz)
        history = st.session_state.ringo_messages[-1:] if st.session_state.ringo_messages else []
        res = model.generate_content([prompt, *history, audio_part])
        return res.text
    except Exception as e:
        return f"Fehler: {str(e)}"

# --- 5. OBERFLÄCHE ---
st.title("🏯 Onkel Ringos Lernapp")

with st.sidebar:
    st.markdown("### 📍 Location")
    current_ort = st.selectbox("Wähle den Ort:", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus Arima Onsen"])
    if st.button("Gespräch Reset"):
        st.session_state.ringo_messages = []
        st.session_state.last_rec_id = None
        st.rerun()

# Verlauf anzeigen
for i, nachricht in enumerate(st.session_state.ringo_messages):
    st.divider()
    
    parts = {"s": "", "j": ""}
    if "STEFAN:" in nachricht and "JAPANISCH:" in nachricht:
        parts["s"] = nachricht.split("STEFAN:")[1].split("JAPANISCH:")[0].strip()
        parts["j"] = nachricht.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip()

    if parts["s"]:
        st.markdown(f'<div class="transcript-style">Onkel Ringo verstand: "{parts["s"]}"</div>', unsafe_allow_html=True)

    if parts["j"]:
        try:
            tts = gTTS(text=parts["j"], lang='ja')
            audio_io = io.BytesIO()
            tts.write_to_fp(audio_io)
            b64_str = base64.b64encode(audio_io.getvalue()).decode()
            is_latest = (i == len(st.session_state.ringo_messages) - 1)
            autoplay = "autoplay" if is_latest else ""
            st.markdown(f'<audio src="data:audio/mp3;base64,{b64_str}" controls {autoplay}></audio>', unsafe_allow_html=True)
        except: pass

    with st.expander("👁️ Lösung anzeigen"):
        st.markdown(f'<div class="ringo-response">{nachricht}</div>', unsafe_allow_html=True)

# Mikrofon
st.write("---")
st.write("### 🎤 Sprich jetzt:")
rec_audio = audio_recorder(text="", icon_size="3x", pause_threshold=3.0, key="ringo_v25_final")

if rec_audio and rec_audio != st.session_state.last_rec_id:
    st.session_state.last_rec_id = rec_audio
    with st.spinner("Onkel Ringo denkt nach..."):
        antwort = process_interaction(rec_audio, current_ort)
        st.session_state.ringo_messages.append(antwort)
        st.rerun()

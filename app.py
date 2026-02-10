import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- 1. INITIALISIERUNG & DESIGN ---
st.set_page_config(page_title="Onkel Ringos Japan-Training", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f4e7d3 !important; }
    h1 { color: #002b5b !important; border-bottom: 5px solid #bc002d !important; padding-bottom: 10px; }
    
    .seller-bubble { 
        font-size: 1.2rem !important; color: #ffffff !important; 
        background-color: #002b5b !important; padding: 20px; 
        border-radius: 0 20px 20px 20px; border-left: 10px solid #bc002d;
        margin: 15px 0; box-shadow: 4px 4px 10px rgba(0,0,0,0.1);
    }
    
    .stefan-text { font-size: 1.1rem; color: #bc002d; font-weight: bold; margin-top: 20px; }

    /* Mikrofon-Zentrierung */
    div[data-testid="stVerticalBlock"] > div:has(svg) {
        display: flex !important; justify-content: center !important; 
        transform: scale(1.5); margin: 30px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. KI MODELL KONFIGURATION ---
@st.cache_resource
def get_model():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("API Key fehlt in den Secrets!")
        return None
    genai.configure(api_key=api_key)
    # Nutze das stabile Flash-Modell für schnelle Antworten
    return genai.GenerativeModel('gemini-1.5-flash')

# --- 3. SESSION STATE ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # Für den KI-Kontext
if "display_history" not in st.session_state:
    st.session_state.display_history = []  # Für die UI-Anzeige
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None

def ask_ai(audio_bytes, ort):
    model = get_model()
    if not model: return "Fehler: Keine API Verbindung."
    
    system_instruction = (
        f"Du bist eine sehr höfliche japanische Verkäuferin in {ort}. Stefan ist ein Ausländer, der Japanisch lernt. "
        "DEIN VERHALTEN: "
        "1. Sei herzlich und geduldig (Omotenashi-Stil). "
        "2. Antworte in einfachem Japanisch, maximal 2 Sätze pro Antwort. "
        "3. Stelle am Ende IMMER genau EINE höfliche Frage, um das Gespräch voranzubringen. "
        "4. ABLAUF: Begrüßung -> Herkunft klären -> Bestellung aufnehmen -> Zubereitung/Warten (O-machido-sama) -> Abschied/Smalltalk. "
        "FORMAT DER ANTWORT (STRENG EINHALTEN): "
        "STEFAN: [Was er auf Deutsch oder Japanisch gesagt hat] "
        "JAPANISCH: [Deine Antwort + Frage auf Japanisch] "
        "DEUTSCH: [Übersetzung deiner Antwort]"
    )
    
    try:
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        # Wir übergeben die letzten 6 Nachrichten für den Kontext
        content_to_send = [system_instruction] + st.session_state.chat_history[-6:] + [audio_part]
        res = model.generate_content(content_to_send)
        
        # Antwort im Kontext speichern
        st.session_state.chat_history.append(res.text)
        return res.text
    except Exception as e:
        return f"Fehler bei der KI-Verarbeitung: {str(e)}"

# --- 4. HAUPT-UI ---
st.title("🏯 Rollenspiel: Japanische Verkäuferin")

with st.sidebar:
    st.write("### ⚙️ Einstellungen")
    place = st.selectbox("Ort des Geschehens:", ["Metzgerei Takezono (Ashiya)", "McDonald's", "Kleiner Buchladen", "Arima Onsen Busstopp"])
    if st.button("Gespräch zurücksetzen"):
        st.session_state.chat_history = []
        st.session_state.display_history = []
        st.session_state.last_audio_hash = None
        st.rerun()
    st.info("Tipp: Klicke auf das Schloss in der Browser-Leiste, um das Mikrofon dauerhaft zu erlauben.")

# Chat-Verlauf anzeigen
for i, entry in enumerate(st.session_state.display_history):
    # Parsing der Antwortteile
    stefan_text = "..."
    japanisch_text = ""
    deutsch_text = ""
    
    if "STEFAN:" in entry and "JAPANISCH:" in entry:
        stefan_text = entry.split("STEFAN:")[1].split("JAPANISCH:")[0].strip()
        japanisch_text = entry.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip()
        deutsch_text = entry.split("DEUTSCH:")[1].strip() if "DEUTSCH:" in entry else ""

    # UI Block
    st.markdown(f'<div class="stefan-text">👤 Stefan: „{stefan_text}“</div>', unsafe_allow_html=True)
    
    if japanisch_text:
        col1, col2 = st.columns([1, 10])
        with col2:
            # TTS Audio generieren
            try:
                tts = gTTS(text=japanisch_text, lang='ja')
                audio_buffer = io.BytesIO()
                tts.write_to_fp(audio_buffer)
                b64_audio = base64.b64encode(audio_buffer.getvalue()).decode()
                # Nur die letzte Nachricht spielt automatisch ab
                is_last = (i == len(st.session_state.display_history) - 1)
                auto_play = "autoplay" if is_last else ""
                st.markdown(f'<audio src="data:audio/mp3;base64,{b64_audio}" controls {auto_play}></audio>', unsafe_allow_html=True)
            except:
                st.error("Audio konnte nicht geladen werden.")
        
        with st.expander("Übersetzung & Text anzeigen"):
            st.markdown(f'<div class="seller-bubble"><b>JP:</b> {japanisch_text}<br><br><b>DE:</b> {deutsch_text}</div>', unsafe_allow_html=True)

# --- 5. AUDIO RECORDER (UNTERER BEREICH) ---
st.write("---")
st.write("### 🎤 Antworte der Verkäuferin:")

# pause_threshold auf 2.5 Sekunden gesetzt für entspanntes Sprechen
audio_data = audio_recorder(
    text="Klicke zum Sprechen",
    icon_size="3x",
    pause_threshold=2.5,
    key="japan_mic_v1"
)

if audio_data:
    # Hash prüfen, um Doppel-Trigger zu vermeiden
    current_hash = hash(audio_data)
    if st.session_state.last_audio_hash != current_hash:
        st.session_state.last_audio_hash = current_hash
        with st.spinner("Die Dame hört zu..."):
            ai_response = ask_ai(audio_data, place)
            st.session_state.display_history.append(ai_response)
            st.rerun()

import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
import base64

# 1. iPad Pro Optimierung (Modell ML0N2FD/A)
st.set_page_config(page_title="Japanisch Trainer", layout="wide")

st.markdown("""
    <style>
    /* XXL Schrift für das 12,9" Display */
    .stMarkdown p { font-size: 1.6rem !important; line-height: 1.7; }
    /* Großer Audio-Player */
    audio { width: 100% !important; height: 60px !important; margin: 15px 0; }
    /* Chat-Eingabe vergrößern */
    .stChatInput input { font-size: 1.5rem !important; padding: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🇯🇵 Japanisch Trainer")

# 2. Sidebar & KI Setup
st.sidebar.header("Einstellungen")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

if not api_key:
    st.info("Bitte gib deinen API-Key in der Seitenleiste ein.")
    st.stop()

# Ortswahl
situation = st.sidebar.radio(
    "Wo bist du gerade?",
    ["Metzgerei Takezono", "McDonald's Ashiya", "Bus nach Arima Onsen"]
)

# KI-Verbindung
genai.configure(api_key=api_key)

@st.cache_resource
def get_model():
    try:
        model_namen = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if model_namen:
            return genai.GenerativeModel(model_namen[0])
        return None
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
        return None

model = get_model()

# 3. Audio-Funktion (Robust für iPad)
def erzeuge_audio_html(text):
    try:
        # Nur den japanischen Teil extrahieren
        if "JAPANISCH:" in text:
            jp_teil = text.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip()
        else:
            jp_teil = text
        
        tts = gTTS(text=jp_teil, lang='ja')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        b64 = base64.b64encode(audio_io.getvalue()).decode()
        
        return f"""
            <div style="background:#f1f3f4; padding:15px; border-radius:15px;">
                <audio controls autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>
            </div>
        """
    except: return None

# 4. Chat-Logik & Automatische Begrüßung
if "messages" not in st.session_state:
    st.session_state.messages = []

# Prüfen, ob der Ort gewechselt wurde
if "current_sit" not in st.session_state:
    st.session_state.current_sit = None

if st.session_state.current_sit != situation:
    st.session_state.current_sit = situation
    st.session_state.messages = [] # Verlauf leeren für neuen Ort
    
    # Automatische Begrüßung durch die KI triggern
    welcome_prompt = (
        f"Du bist ein Mitarbeiter bei {situation}. Stefan (48, Mathelehrer) betritt gerade den Laden/Bus. "
        "Begrüße ihn höflich auf Japanisch und frage ihn, was er möchte. "
        "Antworte IMMER so:\nJAPANISCH: [Satz]\nDEUTSCH: [Übersetzung]"
    )
    
    try:
        response = model.generate_content(welcome_prompt)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except:
        st.error("Fehler beim Starten des Gesprächs.")

# Chat Verlauf anzeigen
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant":
            player = erzeuge_audio_html(msg["content"])
            if player: st.markdown(player, unsafe_allow_html=True)

# 5. Eingabe über Tastatur (mit Mikrofon-Symbol auf dem iPad)
if user_input := st.chat_input("Antworte dem Personal..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Prompt für die laufende Unterhaltung
    SYSTEM_PROMPT = (
        f"Du bist Mitarbeiter bei {situation}. Stefan spricht Japanisch. "
        "Antworte IMMER exakt so:\n"
        "STEFAN SAGTE (AUF DEUTSCH): [Übersetzung von Stefan]\n"
        "JAPANISCH: [Deine Antwort]\n"
        "DEUTSCH: [Übersetzung deiner Antwort]"
    )
    
    try:
        response = model.generate_content(f"{SYSTEM_PROMPT}\nStefan sagt: {user_input}")
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        st.rerun() # Seite neu laden, um Audio zu triggern
    except Exception as e:
        st.error(f"Fehler: {e}")

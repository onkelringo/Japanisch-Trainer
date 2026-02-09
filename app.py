import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
import base64

# 1. iPad Pro Optimierung (Kein unsichtbarer Code!)
st.set_page_config(page_title="Japanisch Trainer", layout="wide")

st.markdown("""
    <style>
    /* XXL Schrift für das 12,9" Display */
    .stMarkdown p { font-size: 1.6rem !important; line-height: 1.7; }
    /* Großer Audio-Player */
    audio { width: 100% !important; height: 60px !important; margin: 15px 0; }
    /* Chat-Eingabe deutlich sichtbar machen */
    .stChatInput input { font-size: 1.5rem !important; padding: 15px !important; border: 2px solid #ff4b4b !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🇯🇵 Japanisch Trainer")

# 2. Sidebar & KI Setup
st.sidebar.header("Einstellungen")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

if not api_key:
    st.info("Bitte gib zuerst links deinen API-Key ein, Stefan.")
    st.stop()

# Ortswahl (Startpunkt)
st.sidebar.divider()
situation = st.sidebar.selectbox(
    "Wähle deine Situation zum Starten:",
    ["Bitte wählen...", "Metzgerei Takezono", "McDonald's Ashiya", "Bus nach Arima Onsen"]
)

if situation == "Bitte wählen...":
    st.warning("Wähle links in der Liste einen Ort aus, um das Gespräch zu beginnen!")
    st.stop()

# KI-Verbindung
genai.configure(api_key=api_key)

@st.cache_resource
def get_model():
    try:
        model_namen = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if model_namen:
            # WICHTIG: Nimmt das erste verfügbare Modell als String
            return genai.GenerativeModel(model_namen[0])
        return None
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
        return None

model = get_model()

# 3. Audio-Funktion (Base64 für iPad Safari)
def erzeuge_audio_html(text):
    try:
        if "JAPANISCH:" in text:
            jp_teil = text.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip()
        else:
            jp_teil = text
        
        tts = gTTS(text=jp_teil, lang='ja')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        b64 = base64.b64encode(audio_io.getvalue()).decode()
        
        return f'<audio controls autoplay style="width:100%; height:60px;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    except: return None

# 4. Chat-Logik & Automatische Begrüßung
if "messages" not in st.session_state:
    st.session_state.messages = []

if "current_sit" not in st.session_state or st.session_state.current_sit != situation:
    st.session_state.current_sit = situation
    st.session_state.messages = [] # Reset bei neuem Ort
    
    # Die KI startet das Gespräch
    welcome_prompt = (
        f"Du bist ein Mitarbeiter bei {situation}. Stefan (48, Mathelehrer) betritt gerade den Ort. "
        "Begrüße ihn höflich auf Japanisch und frage ihn, was er möchte. "
        "Antworte IMMER so:\nJAPANISCH: [Satz]\nDEUTSCH: [Übersetzung]"
    )
    
    try:
        response = model.generate_content(welcome_prompt)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except:
        st.error("KI-Dienst momentan nicht erreichbar.")

# Chat Verlauf anzeigen
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant":
            player = erzeuge_audio_html(msg["content"])
            if player: st.markdown(player, unsafe_allow_html=True)

# 5. Die Tastatur-Eingabe (Standard Streamlit Chat Input)
if user_input := st.chat_input("Tippe hier und nutze das Tastatur-Mikrofon..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Prompt für Stefan als Mathelehrer
    SYSTEM_PROMPT = (
        f"Du bist Mitarbeiter bei {situation}. Stefan (Mathelehrer) spricht Japanisch. "
        "Antworte IMMER so:\n"
        "STEFAN SAGTE (AUF DEUTSCH): [Übersetzung von Stefan]\n"
        "JAPANISCH: [Deine Antwort]\n"
        "DEUTSCH: [Übersetzung deiner Antwort]"
    )
    
    try:
        response = model.generate_content(f"{SYSTEM_PROMPT}\nStefan sagt: {user_input}")
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        st.rerun() 
    except Exception as e:
        st.error(f"Fehler: {e}")
import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io

# 1. Grundkonfiguration
st.set_page_config(page_title="Stefans Japan-Trainer", page_icon="🇯🇵")

# XXL-Design für iPhone/iPad (Großer Audio-Player & Schrift)
st.markdown("""
    <style>
    audio { width: 100% !important; height: 50px; }
    .stMarkdown p { font-size: 1.2rem !important; }
    .stButton button { width: 100%; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏯 Stefans Japan-Trainer")

# 2. Seitenleiste (Sidebar)
st.sidebar.header("Einstellungen")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

if not api_key:
    st.info("Bitte gib deinen API-Key in der Seitenleiste ein.")
    st.stop()

st.sidebar.divider()
situation = st.sidebar.radio(
    "Wo bist du gerade?",
    ["Metzgerei Takezono", "McDonald's Ashiya", "Bus nach Arima Onsen"]
)

# 3. KI-Verbindung (Fix für TypeError)
genai.configure(api_key=api_key)

@st.cache_resource
def get_model():
    try:
        # Wir holen die Liste und nehmen EXAKT das erste Element (String)
        model_namen = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if model_namen:
            # WICHTIG: [0] stellt sicher, dass es ein Text ist, keine Liste!
            return genai.GenerativeModel(model_namen[0])
        return None
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
        return None

model = get_model()

# 4. System-Anweisung (Prompt)
SYSTEM_PROMPT = (
    f"Du bist ein Mitarbeiter bei: {situation}. "
    "Dein Gesprächspartner ist Stefan (48, Mathelehrer). "
    "Antworte IMMER in diesem Format:\n\n"
    "JAPANISCH: [Satz]\n"
    "DEUTSCH: [Übersetzung/Korrektur]\n"
)

# 5. Stabile Audio-Funktion (Fix für Split-Error)
def erzeuge_audio(text):
    try:
        # Wir filtern nur den japanischen Teil heraus
        if "DEUTSCH:" in text:
            # Nimm alles VOR "DEUTSCH:"
            jp_teil = text.split("DEUTSCH:")[0]
        else:
            jp_teil = text
        
        # Entferne das Label "JAPANISCH:" für die Sprachausgabe
        jp_sauber = jp_teil.replace("JAPANISCH:", "").strip()
        
        if not jp_sauber:
            return None

        tts = gTTS(text=jp_sauber, lang='ja')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        return audio_io.getvalue()
    except Exception:
        return None

# 6. Chat-Logik
if "messages" not in st.session_state:
    st.session_state.messages = []

# Reset bei Ortswechsel
if "last_sit" not in st.session_state or st.session_state.last_sit != situation:
    st.session_state.messages = []
    st.session_state.last_sit = situation

# Verlauf anzeigen
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 7. Eingabe & Antwort
if user_input := st.chat_input("Schreib Stefan..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    voller_kontext = f"{SYSTEM_PROMPT}\nStefan sagt: {user_input}"
    
    with st.chat_message("assistant"):
        try:
            response = model.generate_content(voller_kontext)
            ai_text = response.text
            st.write(ai_text)
            
            # Audio erzeugen
            audio_daten = erzeuge_audio(ai_text)
            if audio_daten:
                st.audio(audio_daten, format="audio/mp3")
            
            st.session_state.messages.append({"role": "assistant", "content": ai_text})
        except Exception as e:
            st.error(f"Fehler: {e}")

st.sidebar.divider()
st.sidebar.write(f"Aktuelle Szene: **{situation}**")
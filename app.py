import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io

# 1. Einfaches, stabiles Design
st.set_page_config(page_title="Stefans Japan-Trainer", page_icon="🇯🇵")

# Korrektur der CSS-Zeile (jetzt fehlerfrei)
st.markdown("""
    <style>
    audio { width: 100% !important; height: 45px; }
    .stMarkdown p { font-size: 1.1rem !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏯 Stefans Japan-Trainer")

# 2. Sidebar für API-Key und Orte
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

# 3. KI-Verbindung
genai.configure(api_key=api_key)

@st.cache_resource
def get_model():
    try:
        # Sucht das erste Modell, das Content generieren kann
        model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Wir nehmen das erste verfügbare (meist gemini-1.5-flash oder gemini-pro)
        return genai.GenerativeModel(model_list[0])
    except Exception as e:
        st.error(f"KI-Verbindungsfehler: {e}")
        return None

model = get_model()

# 4. System Prompt (Klarer Befehl an die KI)
SYSTEM_PROMPT = (
    f"Du bist ein Mitarbeiter bei: {situation}. "
    "Dein Gesprächspartner ist Stefan (48, Mathelehrer). "
    "Antworte IMMER exakt in diesem Format:\n\n"
    "JAPANISCH: [Hier der japanische Satz]\n"
    "DEUTSCH: [Hier die Übersetzung oder Korrektur]\n"
)

# 5. Stabile Audio-Funktion
def erzeuge_audio(text):
    try:
        # Wir filtern den japanischen Teil für die Sprachausgabe
        if "DEUTSCH:" in text:
            jp_clean = text.split("DEUTSCH:")[0]
        else:
            jp_clean = text
        
        jp_clean = jp_clean.replace("JAPANISCH:", "").strip()
        
        if not jp_clean:
            return None

        tts = gTTS(text=jp_clean, lang='ja')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        return audio_io.getvalue()
    except:
        return None

# 6. Chat-Logik
if "messages" not in st.session_state:
    st.session_state.messages = []

# Reset bei Ortswechsel
if "last_sit" not in st.session_state or st.session_state.last_sit != situation:
    st.session_state.messages = []
    st.session_state.last_sit = situation

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
            audio_data = erzeuge_audio(ai_text)
            if audio_data:
                st.audio(audio_data, format="audio/mp3")
            
            st.session_state.messages.append({"role": "assistant", "content": ai_text})
        except Exception as e:
            st.error(f"Antwort-Fehler: {e}")
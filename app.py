import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io

# 1. Seite & Design
st.set_page_config(page_title="Stefans Japan-Trainer", page_icon="🇯🇵")
st.title("🏯 Stefans Japanisch-Trainer")

# 2. Seitenleiste: Key & Orte
st.sidebar.header("Einstellungen")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

if not api_key:
    st.info("Bitte gib deinen API-Key in der Seitenleiste ein.", icon="🔑")
    st.stop()

st.sidebar.divider()
situation = st.sidebar.radio(
    "Wo bist du gerade?",
    ["Metzgerei Takezono", "McDonald's Ashiya", "Bus nach Arima Onsen"]
)

# 3. KI-Modell laden
genai.configure(api_key=api_key)

@st.cache_resource
def get_model():
    try:
        # Dynamische Suche nach dem besten Modell (Flash ist am schnellsten für Sprache)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = 'models/gemini-1.5-flash'
        return genai.GenerativeModel(target if target in models else models[0])
    except:
        return None

model = get_model()

# 4. Spezifische Prompts (Damit Japanisch UND Deutsch kommen)
prompts = {
    "Metzgerei Takezono": "Du bist die nette Verkäuferin bei Takezono. Stefan (48) möchte etwas kaufen.",
    "McDonald's Ashiya": "Du bist Mitarbeiter bei McDonald's Ashiya am Bahnhof.",
    "Bus nach Arima Onsen": "Du bist der Busfahrer an der Haltestelle nach Arima Onsen."
}

# WICHTIG: Die Anweisung für BEIDE Sprachen
SYSTEM_PROMPT = (
    f"{prompts[situation]} "
    "Antworte Stefan-san immer in zwei Teilen:\n"
    "1. Der japanische Satz (Höflich).\n"
    "2. Eine kurze deutsche Übersetzung/Korrektur.\n"
    "Schreibe dazwischen drei Bindestriche (---)."
)

# 5. Audio-Funktion (Robust für iOS/iPhone)
def erzeuge_audio(text):
    try:
        # Wir nehmen nur den japanischen Teil (vor den Bindestrichen) für die Stimme
        japanischer_teil = text.split('---')[0].strip()
        tts = gTTS(text=japanischer_teil, lang='ja')
        
        # In Bytes schreiben
        audio_file = io.BytesIO()
        tts.write_to_fp(audio_file)
        return audio_file.getvalue() # Gibt die fertigen Daten zurück
    except Exception as e:
        return None

# 6. Chat-Verlauf
if "messages" not in st.session_state:
    st.session_state.messages = []

# Reset bei Situationswechsel
if "last_sit" not in st.session_state or st.session_state.last_sit != situation:
    st.session_state.messages = []
    st.session_state.last_sit = situation

# Verlauf anzeigen
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 7. Eingabe & Antwort
if user_input := st.chat_input("Sprich mit dem Personal..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    voller_kontext = f"{SYSTEM_PROMPT}\nStefan sagt: {user_input}"
    
    with st.chat_message("assistant"):
        try:
            response = model.generate_content(voller_kontext)
            antwort_text = response.text
            st.write(antwort_text) # Zeigt Japanisch UND Deutsch an
            
            # Audio-Teil
            audio_bytes = erzeuge_audio(antwort_text)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
            
            st.session_state.messages.append({"role": "assistant", "content": antwort_text})
        except Exception as e:
            st.error(f"Fehler: {e}")

st.sidebar.divider()
st.sidebar.info(f"Ort: {situation}")

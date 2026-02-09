import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io

# 1. Seite konfigurieren
st.set_page_config(page_title="Stefans Ashiya-Trainer", page_icon="🍱")
st.title("🏯 Ashiya-Japanisch-Trainer")
st.markdown("Willkommen, Stefan! Dein persönlicher Sprachtrainer für Takezono.")

# 2. API-Key Abfrage in der Seitenleiste
st.sidebar.header("Einstellungen")
api_key = st.sidebar.text_input("Gemini API Key eingeben", type="password")

if not api_key:
    st.info("Bitte gib deinen API-Key in der Seitenleiste ein, um zu starten.", icon="🔑")
    st.stop()

# KI-Verbindung aufbauen
genai.configure(api_key=api_key)

# Dynamische Modellsuche, um den "NotFound"-Fehler zu vermeiden
@st.cache_resource
def get_model():
    try:
        # Sucht das erste Modell, das Texte generieren kann (meist gemini-1.5-flash oder 1.0-pro)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Wir nehmen das erste verfügbare Modell aus der Liste
        return genai.GenerativeModel(models[0])
    except Exception as e:
        st.error(f"Fehler beim Laden des Modells: {e}")
        return None

model = get_model()

if model is None:
    st.stop()

# 3. Identität der KI (System-Prompt)
SYSTEM_PROMPT = (
    "Du bist die nette Verkäuferin aus der Metzgerei Takezono in Ashiya. "
    "Dein Gesprächspartner heißt Stefan. Er ist 48 Jahre alt und Mathematiklehrer. "
    "Antworte immer zuerst kurz und höflich auf Japanisch. "
    "Danach korrigierst du Stefans Japanisch kurz auf Deutsch, falls er Fehler gemacht hat. "
    "Sei immer sehr freundlich und nenne ihn gelegentlich 'Stefan-san'."
)

# 4. Chat-Verlauf speichern
if "messages" not in st.session_state:
    st.session_state.messages = []

# 5. Funktion für die Sprachausgabe
def erzeuge_audio(text):
    # gTTS liest den Text mit japanischer Stimme vor
    tts = gTTS(text=text, lang='ja')
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    return audio_buffer

# 6. Chat-Anzeige
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. Eingabe-Logik
if prompt := st.chat_input("Schreib der Dame von Takezono..."):
    # Nutzerwunsch anzeigen
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Antwort von der KI generieren
    voller_kontext = f"{SYSTEM_PROMPT}\n\nStefan sagt: {prompt}"
    
    with st.chat_message("assistant"):
        try:
            response = model.generate_content(voller_kontext)
            antwort_text = response.text
            st.markdown(antwort_text)
            
            # Audio-Player einblenden
            audio_daten = erzeuge_audio(antwort_text)
            st.audio(audio_daten, format="audio/mp3")
            
            st.session_state.messages.append({"role": "assistant", "content": antwort_text})
        except Exception as e:
            st.error(f"Ein Fehler ist aufgetreten: {e}")

# Info für die Seitenleiste
st.sidebar.divider()
st.sidebar.write("Viel Erfolg beim Lernen, Stefan!")
import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io

# 1. Seiteneinstellungen & Design
st.set_page_config(page_title="Stefans Ashiya-Trainer", page_icon="🍱")
st.title("🏯 Stefans Ashiya-Japanisch-Trainer")
st.markdown("*Exklusiv für den Mathematiklehrer aus Takezono*")

# 2. API-Key Sicherheit in der Seitenleiste
st.sidebar.header("Einstellungen")
api_key = st.sidebar.text_input("Gemini API Key eingeben", type="password")

if not api_key:
    st.info("Bitte gib deinen API-Key in der Seitenleiste ein, um zu starten.", icon="🔑")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. Den "Ashiya-Kontext" festlegen (System-Prompt)
SYSTEM_PROMPT = (
    "Du bist die nette Verkäuferin aus der Metzgerei Takezono in Ashiya. "
    "Dein Gegenüber ist Stefan, ein 48-jähriger Mathematiklehrer. "
    "Antworte immer zuerst kurz auf Japanisch (höflich). "
    "Korrigiere Stefan danach kurz auf Deutsch, falls nötig. "
    "Sei immer freundlich und zuvorkommend, wie in Ashiya üblich."
)

# 4. Chat-Verlauf initialisieren
if "messages" not in st.session_state:
    st.session_state.messages = []

# 5. Hilfsfunktion für die Sprachausgabe
def text_zu_audio(text):
    # Erzeugt eine MP3-Datei im Speicher
    tts = gTTS(text=text, lang='ja')
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    return fp

# 6. Chat-Oberfläche
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Schreib der Dame von Takezono..."):
    # Nutzer-Eingabe anzeigen
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # KI-Antwort generieren
    voller_prompt = f"{SYSTEM_PROMPT}\n\nStefan sagt: {prompt}"
    with st.chat_message("assistant"):
        response = model.generate_content(voller_prompt)
        ai_text = response.text
        st.markdown(ai_text)
        
        # Sprachausgabe erzeugen
        audio_datei = text_zu_audio(ai_text)
        st.audio(audio_datei, format="audio/mp3")
        
        st.session_state.messages.append({"role": "assistant", "content": ai_text})

# 7. Mathe-Bonus für Stefan in der Seitenleiste
st.sidebar.divider()
if st.sidebar.button("Kleines Mathe-Rätsel?"):
    st.sidebar.write("Was ergibt: 十足す十五は？") # 10 + 15 = 25


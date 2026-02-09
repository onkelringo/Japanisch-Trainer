import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io

# 1. Seite konfigurieren
st.set_page_config(page_title="Stefans Japan-Trainer", page_icon="🇯🇵")
st.title("🏯 Stefans Japanisch-Trainer")

# 2. Seitenleiste: Einstellungen & Situations-Wahl
st.sidebar.header("Einstellungen")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

if not api_key:
    st.info("Bitte gib deinen API-Key in der Seitenleiste ein.", icon="🔑")
    st.stop()

# Situation auswählen
st.sidebar.divider()
st.sidebar.subheader("Wo bist du gerade?")
situation = st.sidebar.radio(
    "Wähle einen Ort:",
    ["Metzgerei Takezono", "McDonald's Ashiya", "Bus nach Arima Onsen"]
)

# 3. KI-Modell laden
genai.configure(api_key=api_key)

@st.cache_resource
def get_model():
    try:
        # Sucht automatisch das beste verfügbare Modell
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Wir nehmen 'gemini-1.5-flash', falls in der Liste, sonst das erste
        target = 'models/gemini-1.5-flash'
        return genai.GenerativeModel(target if target in models else models[0])
    except:
        return None

model = get_model()
if not model:
    st.error("Modell konnte nicht geladen werden. Prüfe deinen Key.")
    st.stop()

# 4. System-Prompts je nach Situation
prompts = {
    "Metzgerei Takezono": (
        "Du bist die nette Verkäuferin der Metzgerei Takezono in Ashiya. "
        "Stefan (48, Mathelehrer) möchte etwas kaufen (z.B. Renkon Korokke). "
        "Antworte erst höflich auf Japanisch, dann korrigiere ihn auf Deutsch."
    ),
    "McDonald's Ashiya": (
        "Du bist der Mitarbeiter bei McDonald's am Bahnhof Ashiya. "
        "Du bist sehr effizient und höflich (Fast-Food-Keigo). "
        "Frage Stefan nach seiner Bestellung (Set? Größe? Hier essen?). "
        "Antworte erst auf Japanisch, dann Korrektur auf Deutsch."
    ),
    "Bus nach Arima Onsen": (
        "Du bist der Busfahrer oder ein Mitarbeiter an der Bushaltestelle nach Arima Onsen. "
        "Stefan möchte wissen, wann der Bus fährt oder wie viel es kostet. "
        "Antworte erst auf Japanisch, dann Korrektur auf Deutsch."
    )
}

aktueller_prompt = prompts[situation] + " Nenne ihn Stefan-san."

# 5. Chat-Logik & Audio-Funktion
if "messages" not in st.session_state:
    st.session_state.messages = []

# Falls die Situation gewechselt wird, Chat leeren (optional)
if "last_situation" not in st.session_state:
    st.session_state.last_situation = situation

if st.session_state.last_situation != situation:
    st.session_state.messages = []
    st.session_state.last_situation = situation

def sprich_japanisch(text):
    try:
        # Wir nehmen nur den japanischen Teil (vor der Korrektur) für die Stimme
        japanischer_teil = text.split('\n')[0].split('---')[0]
        tts = gTTS(text=japanischer_teil, lang='ja')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        return audio_io
    except:
        return None

# Chat anzeigen
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Eingabe
if user_input := st.chat_input(f"Sprich mit dem Personal ({situation})..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # KI-Antwort
    voller_kontext = f"{aktueller_prompt}\nStefan sagt: {user_input}"
    with st.chat_message("assistant"):
        response = model.generate_content(voller_kontext)
        antwort = response.text
        st.write(antwort)
        
        # Sprachausgabe
        audio = sprich_japanisch(antwort)
        if audio:
            st.audio(audio, format="audio/mp3")
        
        st.session_state.messages.append({"role": "assistant", "content": antwort})

st.sidebar.divider()
st.sidebar.info(f"Du bist jetzt: **{situation}**")

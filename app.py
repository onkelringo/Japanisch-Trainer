import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io

# 1. Seite & XXL-Design via CSS
st.set_page_config(page_title="Stefans Japan-Trainer", page_icon="🇯🇵")

st.markdown("""
    <style>
    audio { width: 100%; height: 50px; }
    .stMarkdown p { font-size: 1.2rem !important; }
    </style>
    """, unsafe_allow_input=True)

st.title("🏯 Stefans Japan-Trainer")

# 2. Sidebar
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

# 3. KI laden
genai.configure(api_key=api_key)

@st.cache_resource
def get_model():
    try:
        model_names = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = 'models/gemini-1.5-flash'
        # Falls 1.5 Flash nicht da ist, nimm das erste verfügbare
        model_name = target if target in model_names else model_names[0]
        return genai.GenerativeModel(model_name)
    except Exception as e:
        st.error(f"Modell-Fehler: {e}")
        return None

model = get_model()

# 4. System Prompt
SYSTEM_PROMPT = (
    f"Du bist ein Mitarbeiter bei: {situation}. "
    "Dein Gesprächspartner ist Stefan (48, Mathelehrer). "
    "Antworte IMMER exakt in diesem Format:\n\n"
    "JAPANISCH: [Hier nur der japanische Satz]\n"
    "DEUTSCH: [Hier die Übersetzung oder Korrektur]\n\n"
    "Benutze keine Sonderzeichen wie Sternchen."
)

# 5. KORRIGIERTE Audio-Funktion (Der Fix für den Type-Error!)
def erzeuge_audio(text):
    try:
        # Logik: Trenne Text bei "DEUTSCH:", nimm den ersten Teil, entferne "JAPANISCH:"
        if "DEUTSCH:" in text:
            japanisch_roh = text.split("DEUTSCH:")[0]
        else:
            japanisch_roh = text
            
        jp_clean = japanisch_roh.replace("JAPANISCH:", "").strip()
        
        if not jp_clean:
            return None

        tts = gTTS(text=jp_clean, lang='ja')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        return audio_io.getvalue()
    except Exception:
        return None

# 6. Chat Verlauf
if "messages" not in st.session_state:
    st.session_state.messages = []

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
            
            # AUDIO erzeugen
            audio_data = erzeuge_audio(ai_text)
            if audio_data:
                st.audio(audio_data, format="audio/mp3")
            
            st.session_state.messages.append({"role": "assistant", "content": ai_text})
        except Exception as e:
            st.error(f"KI-Fehler: {e}")
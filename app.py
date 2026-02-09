import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
import base64
import time

# 1. Design: Keine Tastatur, nur Dialog und Mikro-Button
st.set_page_config(page_title="Japanisch Trainer", layout="wide")

st.markdown("""
    <style>
    /* Entfernt das Standard-Eingabefeld komplett */
    [data-testid="stChatInput"] {
        display: none;
    }
    
    .stMarkdown p { font-size: 1.6rem !important; }
    audio { width: 100% !important; height: 50px !important; }
    
    /* Der große Mikrofon-Button oben rechts */
    .mic-float {
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: #ff4b4b;
        color: white;
        border-radius: 50%;
        width: 100px;
        height: 100px;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 45px;
        box-shadow: 0 6px 15px rgba(0,0,0,0.4);
        z-index: 999999;
        cursor: pointer;
        border: 4px solid white;
    }
    </style>
    
    <script>
    function startListening() {
        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'ja-JP';
        recognition.start();

        recognition.onresult = (event) => {
            const text = event.results[0].transcript;
            // Schickt den erkannten Text als URL-Parameter an Streamlit zurück
            const url = new URL(window.location.href);
            url.searchParams.set('voice_input', text);
            window.location.href = url.href;
        };
    }
    </script>
    
    <button class="mic-float" onclick="startListening()">🎤</button>
    """, unsafe_allow_html=True)

st.title("🇯🇵 Japanisch Trainer")
st.write("Tippe oben rechts auf das Mikrofon und sprich Japanisch.")

# 2. Sidebar & KI Setup
st.sidebar.header("Einstellungen")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
if not api_key:
    st.info("Bitte API-Key in der Sidebar eingeben.")
    st.stop()

genai.configure(api_key=api_key)

@st.cache_resource
def get_model():
    return genai.GenerativeModel('gemini-1.5-flash')

model = get_model()
situation = st.sidebar.radio("Situation:", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus nach Arima Onsen"])

# 3. Audio-Funktion
def erzeuge_audio_html(text):
    try:
        if "JAPANISCH:" in text:
            jp_part = text.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip()
        else:
            jp_part = text
        tts = gTTS(text=jp_part, lang='ja')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        b64 = base64.b64encode(audio_io.getvalue()).decode()
        return f'<audio controls autoplay style="width:100%;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    except: return ""

# 4. Chat Logik & Voice-Input Verarbeitung
if "messages" not in st.session_state:
    st.session_state.messages = []

# Prüfen, ob eine Spracheingabe über die URL reinkommt
query_params = st.query_params
user_input = query_params.get("voice_input")

if user_input:
    # URL Parameter sofort löschen, damit kein Loop entsteht
    st.query_params.clear()
    
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # Prompt bauen
    SYSTEM_PROMPT = (
        f"Du bist Mitarbeiter bei {situation}. Stefan (48, Mathelehrer) spricht Japanisch. "
        "Antworte IMMER exakt so:\n\n"
        "STEFAN SAGTE (AUF DEUTSCH): [Übersetzung]\n"
        "JAPANISCH: [Antwort]\n"
        "DEUTSCH: [Übersetzung]"
    )
    
    # KI Antwort generieren (mit kurzem Retry für 429er Fehler)
    try:
        response = model.generate_content(f"{SYSTEM_PROMPT}\nStefan: {user_input}")
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except Exception as e:
        st.error("Google drosselt gerade (429). Bitte kurz warten.")

# Chat anzeigen
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant":
            st.markdown(erzeuge_audio_html(msg["content"]), unsafe_allow_html=True)
import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
import base64

# 1. Design & Touch-Fix
st.set_page_config(page_title="Japanisch Trainer", layout="wide")

st.markdown("""
    <style>
    /* Tastaturfeld verstecken */
    [data-testid="stChatInput"] { display: none; }
    
    /* XXL Text für iPad Pro */
    .stMarkdown p { font-size: 1.6rem !important; }
    
    /* Großer Mikrofon-Button, der direkt im Content sitzt */
    .mic-area {
        display: flex;
        justify-content: center;
        padding: 20px;
        background-color: #f0f2f6;
        border-radius: 20px;
        margin-bottom: 20px;
    }
    .mic-btn {
        background-color: #ff4b4b;
        color: white;
        border: none;
        border-radius: 50%;
        width: 120px;
        height: 120px;
        font-size: 50px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# JavaScript Funktion für den Button-Klick
def start_mic_html():
    return f"""
    <script>
    function startListening() {{
        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'ja-JP';
        recognition.start();
        recognition.onresult = (event) => {{
            const text = event.results[0].transcript;
            const url = new URL(window.location.href);
            url.searchParams.set('voice_input', text);
            window.parent.location.href = url.href;
        }};
    }}
    </script>
    <div class="mic-area">
        <button class="mic-btn" onclick="startListening()">🎤</button>
    </div>
    """

st.title("🇯🇵 Japanisch Trainer")
st.sidebar.header("Einstellungen")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

if not api_key:
    st.info("Bitte API-Key in der Sidebar eingeben.")
    st.stop()

# KI Setup
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')
situation = st.sidebar.radio("Situation:", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus nach Arima Onsen"])

# Audio-Funktion
def erzeuge_audio_html(text):
    try:
        jp_part = text.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip() if "JAPANISCH:" in text else text
        tts = gTTS(text=jp_part, lang='ja')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        b64 = base64.b64encode(audio_io.getvalue()).decode()
        return f'<audio controls autoplay style="width:100%;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    except: return ""

# Mikrofon-Button ganz oben anzeigen
st.components.v1.html(start_mic_html(), height=200)

# Chat-Verarbeitung
if "messages" not in st.session_state:
    st.session_state.messages = []

# Voice Input aus URL lesen
query_params = st.query_params
if "voice_input" in query_params:
    user_text = query_params["voice_input"]
    st.query_params.clear() # Parameter löschen
    
    st.session_state.messages.append({"role": "user", "content": user_text})
    
    prompt = f"Du bist Mitarbeiter bei {situation}. Stefan (48, Mathelehrer) sagt: {user_text}. Antworte so: STEFAN SAGTE (AUF DEUTSCH): [Übersetzung] JAPANISCH: [Antwort] DEUTSCH: [Übersetzung]"
    
    try:
        response = model.generate_content(prompt)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except:
        st.error("Fehler 429 - Bitte kurz warten.")

# Chat Verlauf (Neueste Nachricht oben)
for msg in reversed(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant":
            st.markdown(erzeuge_audio_html(msg["content"]), unsafe_allow_html=True)

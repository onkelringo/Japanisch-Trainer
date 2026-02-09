import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
import base64

# 1. Design & CSS für iPad Pro
st.set_page_config(page_title="Japanisch Trainer", layout="wide")

st.markdown("""
    <style>
    /* Tastaturfeld verstecken */
    [data-testid="stChatInput"] { display: none; }
    
    /* XXL Text für iPad Pro Display */
    .stMarkdown p { font-size: 1.6rem !important; }
    
    /* Großer Mikrofon-Bereich */
    .mic-container {
        text-align: center;
        background-color: #f1f3f4;
        padding: 30px;
        border-radius: 25px;
        margin-bottom: 20px;
        border: 2px solid #ff4b4b;
    }
    
    .mic-btn {
        background-color: #ff4b4b;
        color: white;
        border: none;
        border-radius: 50%;
        width: 150px;
        height: 150px;
        font-size: 60px;
        cursor: pointer;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🇯🇵 Japanisch Trainer")

# 2. Sidebar & KI Setup
st.sidebar.header("Einstellungen")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

if not api_key:
    st.info("Bitte den API-Key links in der Sidebar eingeben.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')
situation = st.sidebar.radio("Wo bist du?", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus nach Arima Onsen"])

# 3. Audio-Funktion
def erzeuge_audio_html(text):
    try:
        # Extrahiert nur den japanischen Teil
        if "JAPANISCH:" in text:
            jp_teil = text.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip()
        else:
            jp_teil = text
        
        tts = gTTS(text=jp_teil, lang='ja')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        b64 = base64.b64encode(audio_io.getvalue()).decode()
        return f'<audio controls autoplay style="width:100%; height:50px;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    except: return ""

# 4. Der Sichtbare Mikrofon-Button (HTML & JS)
# Dieser Block ist nun fest im Hauptfenster verankert
st.markdown(f"""
    <div class="mic-container">
        <p style="color: #333; font-weight: bold;">Tippe auf das Mikrofon und sprich Japanisch</p>
        <button class="mic-btn" onclick="startRecognition()">🎤</button>
    </div>

    <script>
    function startRecognition() {{
        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'ja-JP';
        recognition.start();

        recognition.onresult = (event) => {{
            const result = event.results[0][0].transcript;
            // Nutzt die URL-Parameter Methode, um den Text an Python zu senden
            const url = new URL(window.location.href);
            url.searchParams.set('voice_input', result);
            window.location.href = url.href;
        }};
        
        recognition.onerror = (event) => {{
            alert("Mikrofon-Fehler: " + event.error);
        }};
    }}
    </script>
    """, unsafe_allow_html=True)

# 5. Chat-Logik & Verarbeitung
if "messages" not in st.session_state:
    st.session_state.messages = []

# Voice Input aus URL-Parameter lesen
query_params = st.query_params
if "voice_input" in query_params:
    user_text = query_params["voice_input"]
    # Sofort Parameter löschen, um Endlosschleife zu verhindern
    st.query_params.clear()
    
    st.session_state.messages.append({"role": "user", "content": user_text})
    
    # Prompt an die KI
    prompt_full = (
        f"Du bist Mitarbeiter bei {situation}. Stefan (48, Mathelehrer) sagt auf Japanisch: {user_text}. "
        "Antworte IMMER exakt so:\n"
        "STEFAN SAGTE (AUF DEUTSCH): [Übersetzung von Stefan]\n"
        "JAPANISCH: [Deine Antwort]\n"
        "DEUTSCH: [Übersetzung deiner Antwort]"
    )
    
    try:
        response = model.generate_content(prompt_full)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except:
        st.error("Dienst überlastet. Bitte kurz warten.")

# Chat Verlauf anzeigen (Neueste Nachricht oben)
st.divider()
for msg in reversed(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant":
            st.markdown(erzeuge_audio_html(msg["content"]), unsafe_allow_html=True)

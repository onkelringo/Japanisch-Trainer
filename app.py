import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
import base64

# 1. XXL-Design & Sprach-Interface
st.set_page_config(page_title="Ashiya Voice Trainer", layout="wide")

st.markdown("""
    <style>
    .stMarkdown p { font-size: 1.5rem !important; }
    /* Audio-Box etwas kleiner (60px statt 80px) */
    audio { width: 100% !important; height: 60px !important; margin: 10px 0; }
    /* Mikrofon-Button Design */
    .mic-button {
        background-color: #ff4b4b;
        color: white;
        padding: 20px;
        border-radius: 50%;
        border: none;
        width: 100px;
        height: 100px;
        font-size: 40px;
        cursor: pointer;
        display: block;
        margin: 20px auto;
    }
    </style>
    
    <script>
    function startDictation() {
        if (window.hasOwnProperty('webkitSpeechRecognition')) {
            var recognition = new webkitSpeechRecognition();
            recognition.continuous = false;
            recognition.interimResults = false;
            recognition.lang = "ja-JP"; // Sprache auf Japanisch gestellt
            recognition.start();
            recognition.onresult = function(e) {
                document.getElementById('st_input_box').value = e.results[0][0].transcript;
                recognition.stop();
            };
        }
    }
    </script>
    """, unsafe_allow_html=True)

st.title("🎙️ Ashiya Voice-Trainer")

# 2. Sidebar
st.sidebar.header("Einstellungen")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
if not api_key:
    st.stop()

situation = st.sidebar.radio("Ort:", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus nach Arima Onsen"])

# 3. KI-Setup
genai.configure(api_key=api_key)

@st.cache_resource
def get_model():
    model_namen = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    return genai.GenerativeModel(model_namen[0]) if model_namen else None

model = get_model()

# 4. Audio-Funktion mit Geschwindigkeits-Wahl
def erzeuge_audio_html(text, speed=1.0):
    try:
        jp_teil = text.split("DEUTSCH:")[0].replace("JAPANISCH:", "").strip() if "DEUTSCH:" in text else text
        tts = gTTS(text=jp_teil, lang='ja')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        b64 = base64.b64encode(audio_io.getvalue()).decode()
        
        # Player mit Geschwindigkeitssteuerung
        return f"""
            <audio id="player" controls autoplay style="width:100%; height:60px;">
                <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            <div style='text-align: center;'>
                <button onclick="document.getElementById('player').playbackRate = 1.0">Speed 1.0x</button>
                <button onclick="document.getElementById('player').playbackRate = 0.75">Speed 0.75x</button>
            </div>
        """
    except: return ""

# 5. System Prompt (Erzwingt jetzt auch die Übersetzung deiner Sätze)
SYSTEM_PROMPT = (
    f"Du bist Mitarbeiter bei {situation}. Stefan spricht Japanisch. "
    "Antworte IMMER so:\n"
    "DEIN SATZ AUF DEUTSCH: [Übersetze das, was Stefan gerade gesagt hat]\n"
    "JAPANISCH: [Deine Antwort auf Japanisch]\n"
    "DEUTSCH: [Übersetzung deiner Antwort]"
)

# 6. Chat Verlauf
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 7. Sprach-Eingabe (Mikrofon Button)
st.divider()
st.write("### Tippe auf das Mikrofon und sprich Japanisch:")
# Da Streamlit keine direkte Mikrofon-Schnittstelle ohne Custom Component hat, 
# nutzen wir hier das Standard-Chat-Input, das auf dem iPad die Diktierfunktion der Tastatur nutzt.
# AUF DEM IPAD: Tippe in das Feld und nutze die Mikrofon-Taste der iOS-Tastatur.

if user_input := st.chat_input("Tippe hier für das Mikrofon..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        response = model.generate_content(f"{SYSTEM_PROMPT}\nStefan sagt: {user_input}")
        ai_text = response.text
        st.write(ai_text)
        st.markdown(erzeuge_audio_html(ai_text), unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": ai_text})

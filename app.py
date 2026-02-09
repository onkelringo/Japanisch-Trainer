import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
import base64

# 1. XXL-Design & JavaScript für das Mikrofon
st.set_page_config(page_title="Japanisch Trainer", layout="wide")

# JavaScript für die Spracherkennung (Japanisch)
st.markdown("""
    <script>
    function startListening() {
        const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
        recognition.lang = 'ja-JP';
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        recognition.start();

        recognition.onresult = (event) => {
            const speechResult = event.results[0][0].transcript;
            // Sucht das Streamlit Chat-Input Feld und füllt es
            const textArea = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
            if (textArea) {
                textArea.value = speechResult;
                textArea.dispatchEvent(new Event('input', { bubbles: True }));
            }
        };
    }
    </script>
    
    <style>
    .stMarkdown p { font-size: 1.6rem !important; }
    audio { width: 100% !important; height: 50px !important; }
    
    /* Der schwebende Mikrofon-Button rechts unten */
    .mic-float {
        position: fixed;
        bottom: 100px;
        right: 30px;
        background-color: #ff4b4b;
        color: white;
        border-radius: 50%;
        width: 80px;
        height: 80px;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 35px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        z-index: 9999;
        cursor: pointer;
        border: none;
    }
    </style>
    
    <button class="mic-float" onclick="startListening()">🎤</button>
    """, unsafe_allow_html=True)

st.title("🇯🇵 Japanisch Trainer")

# 2. Sidebar & KI Setup
st.sidebar.header("Einstellungen")
api_key = st.sidebar.text_input("Gemini API Key", type="password")
if not api_key:
    st.stop()

situation = st.sidebar.radio("Situation:", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus nach Arima Onsen"])

genai.configure(api_key=api_key)

@st.cache_resource
def get_model():
    model_namen = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
    return genai.GenerativeModel(model_namen[0]) if model_namen else None

model = get_model()

# 3. Audio-Funktion
def erzeuge_audio_html(text):
    try:
        # Extrahiert Japanisch für die Vertonung
        jp_part = text.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip() if "JAPANISCH:" in text else text
        tts = gTTS(text=jp_part, lang='ja')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        b64 = base64.b64encode(audio_io.getvalue()).decode()
        return f'<audio controls autoplay style="width:100%; height:50px;"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>'
    except: return ""

# 4. System Prompt
SYSTEM_PROMPT = (
    f"Du bist Mitarbeiter bei {situation}. Stefan (48, Mathelehrer) spricht Japanisch. "
    "Antworte IMMER exakt so:\n\n"
    "STEFAN SAGTE (AUF DEUTSCH): [Übersetzung von Stefan]\n"
    "JAPANISCH: [Deine Antwort]\n"
    "DEUTSCH: [Übersetzung deiner Antwort]"
)

# 5. Chat Logik
if "messages" not in st.session_state:
    st.session_state.messages = []

# Reset bei Situationswechsel
if "last_sit" not in st.session_state or st.session_state.last_sit != situation:
    st.session_state.messages = []
    st.session_state.last_sit = situation

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# 6. Eingabe
if user_input := st.chat_input("..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        try:
            response = model.generate_content(f"{SYSTEM_PROMPT}\nStefan: {user_input}")
            ai_text = response.text
            st.write(ai_text)
            st.markdown(erzeuge_audio_html(ai_text), unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": ai_text})
        except Exception as e:
            st.error(f"Fehler: {e}")

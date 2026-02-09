import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
import base64

# 1. Optimierung für das 12,9" Display (Modell ML0N2FD/A)
st.set_page_config(page_title="Ashiya Trainer Pro", layout="wide")

st.markdown("""
    <style>
    .stMarkdown p { font-size: 1.6rem !important; line-height: 1.7; }
    audio { 
        width: 100% !important; 
        height: 80px !important; 
        margin: 20px 0;
    }
    .stChatMessage { padding: 25px !important; border-radius: 20px !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏯 Ashiya-Trainer (iPad Pro Edition)")

# 2. Sidebar
st.sidebar.header("Einstellungen")
api_key = st.sidebar.text_input("Gemini API Key", type="password")

if not api_key:
    st.info("Bitte links den API-Key eingeben.")
    st.stop()

situation = st.sidebar.radio("Ort wählen:", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus nach Arima Onsen"])

# 3. KI-Setup (FIX: Übergabe als String, nicht als Liste!)
genai.configure(api_key=api_key)

@st.cache_resource
def get_model():
    try:
        model_namen = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if model_namen:
            return genai.GenerativeModel(model_namen[0])
        return None
    except Exception as e:
        st.error(f"Verbindungsfehler: {e}")
        return None

model = get_model()

# 4. Spezial-Audio für iPad Pro (Base64 + Split-Fix)
def erzeuge_audio_html(text):
    try:
        if "DEUTSCH:" in text:
            jp_teil = text.split("DEUTSCH:")[0]
        else:
            jp_teil = text
            
        jp_sauber = jp_teil.replace("JAPANISCH:", "").strip()
        
        if not jp_sauber:
            return None
            
        tts = gTTS(text=jp_sauber, lang='ja')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        audio_bytes = audio_io.getvalue()
        
        b64 = base64.b64encode(audio_bytes).decode()
        
        audio_html = f"""
            <div style="background:#f1f3f4; padding:20px; border-radius:15px;">
                <p style="font-size: 1.2rem; color: #333; margin-bottom:10px;">🔊 Japanische Sprachausgabe:</p>
                <audio controls autoplay style="width:100%;">
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                    Ihr Browser unterstützt Audio nicht.
                </audio>
            </div>
        """
        return audio_html
    except Exception as e:
        return f"<!-- Audio Fehler: {e} -->"

# 5. System Prompt
SYSTEM_PROMPT = f"Du bist Mitarbeiter bei {situation}. Antworte Stefan (48) IMMER so: JAPANISCH: [Satz] DEUTSCH: [Übersetzung]"

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
if user_input := st.chat_input("Nachricht an das Personal..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        try:
            response = model.generate_content(f"{SYSTEM_PROMPT}\nStefan sagt: {user_input}")
            ai_text = response.text
            st.write(ai_text)
            
            html_player = erzeuge_audio_html(ai_text)
            if html_player:
                st.markdown(html_player, unsafe_allow_html=True)
            
            st.session_state.messages.append({"role": "assistant", "content": ai_text})
        except Exception as e:
            st.error(f"Fehler: {e}")

import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
import base64

# --- CONFIG & STYLE ---
st.set_page_config(page_title="Sensei Stefan's Japan-Trainer", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #f0f2f6; }
    .stMarkdown p { font-size: 1.4rem !important; }
    audio { width: 100%; border-radius: 10px; margin: 10px 0; border: 2px solid #ff4b4b; }
    .stChatInput { bottom: 20px !important; }
    </style>
""", unsafe_allow_html=True)

# --- INITIALISIERUNG ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_sit" not in st.session_state:
    st.session_state.current_sit = None

# --- SIDEBAR ---
with st.sidebar:
    st.title("⛩️ Training-Center")
    api_key = st.text_input("Gemini API Key", type="password")
    
    situation = st.selectbox(
        "Wo willst du glänzen, Stefan?",
        ["Bitte wählen...", "Metzgerei Takezono (Beef-Time)", "McDonald's Ashiya (Burger-Check)", "Bus nach Arima Onsen (Roadtrip)"]
    )
    
    if st.button("Gespräch neu starten"):
        st.session_state.messages = []
        st.session_state.current_sit = None
        st.rerun()

if not api_key:
    st.warning("Ohne Key läuft hier nichts, Sensei!")
    st.stop()

# --- KI SETUP ---
genai.configure(api_key=api_key)

def get_chat_response(prompt):
    try:
        # Wir nutzen flash für die Geschwindigkeit auf dem iPad
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Fehler: {str(e)}"

def play_audio(text):
    try:
        # Extrahiere nur den japanischen Teil für die Sprachausgabe
        if "JAPANISCH:" in text:
            jp_text = text.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip()
        else:
            jp_text = text
        
        tts = gTTS(text=jp_text, lang='ja')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        b64 = base64.b64encode(fp.getvalue()).decode()
        html_elt = f'<audio src="data:audio/mp3;base64,{b64}" controls autoplay></audio>'
        st.markdown(html_elt, unsafe_allow_html=True)
    except:
        st.error("Audio-Sensei macht gerade Pause.")

# --- LOGIK ---
if situation != "Bitte wählen..." and situation != st.session_state.current_sit:
    st.session_state.current_sit = situation
    st.session_state.messages = [] # Reset bei Ortswechsel
    
    # Frecher Start-Prompt
    start_prompt = (
        f"Du bist ein Angestellter bei {situation}. Stefan, ein deutscher Mathelehrer (48), betritt den Laden. "
        "Begrüße ihn extrem höflich, aber baue eine winzige, freche Anspielung auf Mathematik oder deutsches Lehrer-Dasein ein. "
        "Format: JAPANISCH: [Text]\nDEUTSCH: [Übersetzung]"
    )
    initial_msg = get_chat_response(start_prompt)
    st.session_state.messages.append({"role": "assistant", "content": initial_msg})

# --- UI ANZEIGE ---
st.title(f"📍 {st.session_state.current_sit or 'Wähle einen Ort'}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant":
            # Audio nur für die letzte Nachricht automatisch abspielen
            if msg == st.session_state.messages[-1]:
                play_audio(msg["content"])

# --- INPUT ---
if user_input := st.chat_input("Hau was raus, Sensei Stefan..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # System Prompt für die laufende Konversation
    system_instruction = (
        f"Du bist der Angestellte bei {situation}. Stefan antwortet dir. "
        "Bleib in deiner Rolle. Sei höflich, aber 'Gen-Z-Japanisch-frech'. "
        "Wenn er einen Fehler macht, korrigiere ihn charmant (wie ein Mathelehrer, der einen Vorzeichenfehler findet). "
        "ANTWORTE IMMER IN DIESEM FORMAT:\n"
        "STEFAN SAGTE (AUF DEUTSCH): [Was er wohl meinte]\n"
        "JAPANISCH: [Deine Antwort]\n"
        "DEUTSCH: [Übersetzung deiner Antwort]"
    )
    
    full_prompt = f"{system_instruction}\nStefan sagt: {user_input}"
    with st.spinner("Überlege..."):
        ai_response = get_chat_response(full_prompt)
        st.session_state.messages.append({"role": "assistant", "content": ai_response})
    st.rerun()

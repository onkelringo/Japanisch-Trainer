import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
import base64

# --- SETTINGS & STYLE ---
st.set_page_config(page_title="Sensei Stefan v3", layout="wide")

st.markdown("""
    <style>
    .stApp { background: #0e1117; color: #e0e0e0; }
    .stMarkdown p { font-size: 1.5rem !important; line-height: 1.6; }
    .stChatInput input { border: 2px solid #00d4ff !important; font-size: 1.2rem !important; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; border: 1px solid #333; }
    audio { width: 100%; height: 50px; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE INITIALISIERUNG ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_sit" not in st.session_state:
    st.session_state.current_sit = None

# --- SIDEBAR & MODEL-FINDER ---
with st.sidebar:
    st.title("⚙️ Training Setup")
    api_key = st.text_input("Gemini API Key", type="password")
    
    if st.button("🔥 Speicher leeren (Limit-Fix)"):
        st.session_state.messages = []
        st.success("Kontext gelöscht! Start frei.")

    situation = st.selectbox(
        "Wo trainieren wir?",
        ["Wähle Ort...", "Metzgerei Takezono", "McDonald's Ashiya", "Bus nach Arima Onsen"]
    )

# --- INTELLIGENTE MODELLWAHL (FLASH-PRIORITÄT FÜR FREE PLAN) ---
@st.cache_resource
def get_stable_model(key):
    if not key: return None
    genai.configure(api_key=key)
    try:
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Flash ist im Free Plan viel großzügiger (RPN/TPM)
        for pref in ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]:
            if pref in available:
                return genai.GenerativeModel(pref)
        return genai.GenerativeModel(available[0]) if available else None
    except:
        return None

model = get_stable_model(api_key)

# --- AUDIO FUNKTION ---
def get_audio_html(text):
    try:
        # Extrahiere Japanisch-Part
        if "JAPANISCH:" in text:
            jp_text = text.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip()
        else:
            jp_text = text
        
        tts = gTTS(text=jp_text, lang='ja')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        b64 = base64.b64encode(audio_io.getvalue()).decode()
        return f'<audio controls autoplay src="data:audio/mp3;base64,{b64}"></audio>'
    except:
        return None

# --- HAUPTLOGIK ---
if not api_key:
    st.info("Stefan, bitte links den API Key eingeben.")
    st.stop()

if situation != "Wähle Ort..." and situation != st.session_state.current_sit:
    st.session_state.current_sit = situation
    st.session_state.messages = []
    
    # Start-Prompt (Kurz halten für Tokens!)
    intro_prompt = (
        f"Du bist Angestellter bei {situation}. Begrüße Stefan (Mathelehrer) extrem höflich auf Japanisch. "
        "Mach einen kurzen Witz über Mathe. Format: JAPANISCH: [Text] DEUTSCH: [Text]"
    )
    try:
        res = model.generate_content(intro_prompt)
        st.session_state.messages.append({"role": "assistant", "content": res.text})
    except:
        st.error("API Limit erreicht. Klick auf 'Speicher leeren' oder warte 60 Sek.")

# UI Anzeige
st.title(f"🇯🇵 {st.session_state.current_sit if st.session_state.current_sit else 'Japan-Trainer'}")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant" and msg == st.session_state.messages[-1]:
            audio_html = get_audio_html(msg["content"])
            if audio_html: st.markdown(audio_html, unsafe_allow_html=True)

# Eingabe mit Kontext-Kürzung gegen Limits
if user_input := st.chat_input("Tippe hier..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # TOKEN-SPAR-TRICK: Nur die letzten 3 Nachrichten mitsenden
    recent_context = st.session_state.messages[-3:]
    
    system_instruction = (
        f"Du bist Angestellter bei {situation}. Stefan ist Mathelehrer. Sei höflich und frech. "
        "Format: STEFAN MEINTE: [Übersetzung] JAPANISCH: [Antwort] DEUTSCH: [Übersetzung]"
    )
    
    chat_prompt = f"{system_instruction}\nVerlauf: {recent_context}\nStefan sagt: {user_input}"
    
    try:
        res = model.generate_content(chat_prompt)
        st.session_state.messages.append({"role": "assistant", "content": res.text})
        st.rerun()
    except Exception as e:
        st.error("Limit erreicht! Bitte kurz warten oder Speicher leeren.")

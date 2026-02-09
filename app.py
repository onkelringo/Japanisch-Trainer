import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- API SETUP ---
API_KEY = st.secrets.get("GEMINI_API_KEY")

# --- CLEAN DESIGN (ROT / WEISS / SCHWARZ) ---
st.set_page_config(page_title="Onkel Ringos Lernapp", layout="wide")

st.markdown("""
    <style>
    /* Grundfarben */
    .stApp { background-color: #ffffff; color: #000000; }
    
    /* Hauptcontainer */
    .main .block-container { max-width: 700px; padding: 2rem; margin: auto; }

    /* Überschriften */
    h1 { color: #bc002d !important; border-bottom: 2px solid #bc002d; padding-bottom: 10px; }

    /* Boxen für Chat */
    .stefan-info { font-size: 0.9rem; color: #666; margin-bottom: 5px; }
    .seller-box { 
        font-size: 1.3rem !important; 
        color: #ffffff; 
        background: #000000; 
        padding: 20px; 
        border-radius: 5px; 
        border-left: 10px solid #bc002d;
    }

    /* Mikrofon-Button: Einfaches Rot/Weiss Design */
    div[data-testid="stVerticalBlock"] > div:has(svg) {
        display: flex; justify-content: center; transform: scale(2.0); margin: 40px 0;
    }
    
    /* Sidebar schwarz/weiss */
    section[data-testid="stSidebar"] { background-color: #f0f0f0 !important; }
    
    /* Audio Player */
    audio { width: 100%; border: 1px solid #bc002d; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- KI LOGIK (TOKEN-SPAREND) ---
@st.cache_resource
def get_model(key):
    genai.configure(api_key=key)
    return genai.GenerativeModel('gemini-1.5-flash-8b')

if "chat" not in st.session_state: st.session_state.chat = []
if "last_audio" not in st.session_state: st.session_state.last_audio = None

def ask_ai(audio_bytes, loc):
    model = get_model(API_KEY)
    try:
        audio_info = {"mime_type": "audio/wav", "data": audio_bytes}
        prompt = (f"Du bist Verkäuferin in {loc}. Antworte höflich und kurz. "
                  "Format: STEFAN: [Text] JAPANISCH: [Antwort] DEUTSCH: [Text]")
        # Sende KEINE History um Quota zu sparen
        res = model.generate_content([prompt, audio_info])
        return res.text
    except Exception as e:
        return f"Fehler (Quota?): {str(e)}"

# --- UI ---
st.title("🏯 Onkel Ringos Lernapp")

with st.sidebar:
    st.write("### 📍 Ort")
    sit = st.selectbox("Auswahl:", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus Arima Onsen"])
    if st.button("Verlauf löschen"):
        st.session_state.chat = []
        st.rerun()

# Verlauf (Neu oben oder unten? Hier: Chronologisch nach unten)
for i, msg in enumerate(st.session_state.chat):
    st.divider()
    
    # Inhalte trennen
    parts = {"s": "", "j": ""}
    if "STEFAN:" in msg and "JAPANISCH:" in msg:
        parts["s"] = msg.split("STEFAN:").split("JAPANISCH:").strip()
        parts["j"] = msg.split("JAPANISCH:").split("DEUTSCH:").strip()

    if parts["s"]:
        st.markdown(f'<div class="stefan-info">Stefan sagte: {parts["s"]}</div>', unsafe_allow_html=True)

    if parts["j"]:
        try:
            tts = gTTS(text=parts["j"], lang='ja')
            b = io.BytesIO(); tts.write_to_fp(b)
            b64 = base64.b64encode(b.getvalue()).decode()
            auto = "autoplay" if i == len(st.session_state.chat)-1 else ""
            st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls {auto}></audio>', unsafe_allow_html=True)
        except: pass

    with st.expander("👁️ Antwort lesen"):
        st.markdown(f'<div class="seller-box">{msg}</div>', unsafe_allow_html=True)

# Mikrofon
st.write("---")
audio_data = audio_recorder(text="Tippen zum Sprechen", icon_size="2x", pause_threshold=3.0, key="ringo_mic")

if audio_data and audio_data != st.session_state.last_audio:
    st.session_state.last_audio = audio_data
    with st.spinner("Onkel Ringo hört zu..."):
        ans = ask_ai(audio_data, sit)
        st.session_state.chat.append(ans)
        st.rerun()

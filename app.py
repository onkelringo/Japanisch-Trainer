import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- 1. APP CONFIG (Zwingt Streamlit zum Neuladen) ---
st.set_page_config(page_title="Onkel Ringos Lernapp", layout="wide")

# --- 2. FARB-STYLING (ROT-WEISS-SCHWARZ) ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff !important; }
    .main .block-container { max-width: 700px !important; margin: auto; }
    h1 { color: #bc002d !important; border-bottom: 4px solid #bc002d !important; }
    .seller-box { 
        font-size: 1.4rem !important; color: #ffffff !important; background: #000000 !important; 
        padding: 20px !important; border-radius: 0px !important; border-left: 15px solid #bc002d !important;
    }
    .user-text { font-size: 0.9rem !important; color: #666 !important; }
    div[data-testid="stVerticalBlock"] > div:has(svg) {
        display: flex; justify-content: center; transform: scale(2.5); margin: 50px 0;
    }
    svg { fill: #bc002d !important; }
    section[data-testid="stSidebar"] { background-color: #f8f9fa !important; border-right: 1px solid #eee; }
    </style>
""", unsafe_allow_html=True)

# --- 3. INTELLIGENTE MODELL-AUSWAHL ---
API_KEY = st.secrets.get("GEMINI_API_KEY")

@st.cache_resource
def get_available_model(key):
    if not key: return None
    genai.configure(api_key=key)
    try:
        # Wir testen, welches Modell dein Key akzeptiert
        for model_name in ['gemini-1.5-flash', 'gemini-pro', 'gemini-1.5-flash-8b']:
            try:
                m = genai.GenerativeModel(model_name)
                # Test-Anruf (minimal)
                m.generate_content("test")
                return m
            except:
                continue
        return None
    except:
        return None

# --- 4. SESSION STATE ---
if "ringo_chat" not in st.session_state:
    st.session_state.ringo_chat = []
if "audio_id" not in st.session_state:
    st.session_state.audio_id = None

def get_response(audio_data, loc):
    model = get_available_model(API_KEY)
    if not model: return "Fehler: Kein passendes Gemini-Modell gefunden."
    try:
        audio_part = {"mime_type": "audio/wav", "data": audio_data}
        prompt = (f"Du bist eine japanische Verkäuferin in {loc}. Stefan ist dein Kunde. "
                  "Führe ein echtes Rollenspiel: Antworte höflich und stelle IMMER eine Gegenfrage "
                  "(z.B. nach Menge, Tüte, Bezahlung). "
                  "FORMAT: STEFAN: [Was er sagte] JAPANISCH: [Antwort + Frage] DEUTSCH: [Übersetzung]")
        
        res = model.generate_content([prompt, audio_part])
        return res.text
    except Exception as e:
        return f"Limit/Fehler: {str(e)}"

# --- 5. UI ---
st.title("🏯 Onkel Ringos Lernapp")

with st.sidebar:
    st.markdown("### 📍 Umgebung")
    ort = st.selectbox("Ort:", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus Arima Onsen"])
    if st.button("Reset"):
        st.session_state.ringo_chat = []
        st.rerun()

# Verlauf
for i, msg in enumerate(st.session_state.ringo_chat):
    st.divider()
    parts = {"s": "", "j": ""}
    if "STEFAN:" in msg and "JAPANISCH:" in msg:
        parts["s"] = msg.split("STEFAN:").split("JAPANISCH:").strip()
        parts["j"] = msg.split("JAPANISCH:").split("DEUTSCH:").strip()

    if parts["s"]:
        st.markdown(f'<div class="user-text">Verstanden: "{parts["s"]}"</div>', unsafe_allow_html=True)

    if parts["j"]:
        try:
            tts = gTTS(text=parts["j"], lang='ja')
            audio_io = io.BytesIO()
            tts.write_to_fp(audio_io)
            b64 = base64.b64encode(audio_io.getvalue()).decode()
            auto = "autoplay" if i == len(st.session_state.ringo_chat)-1 else ""
            st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls {auto}></audio>', unsafe_allow_html=True)
        except: pass

    with st.expander("👁️ Lösung anzeigen"):
        st.markdown(f'<div class="seller-box">{msg}</div>', unsafe_allow_html=True)

# Mikrofon
st.write("---")
recorded = audio_recorder(text="", icon_size="3x", pause_threshold=3.0, key="mic_v24")

if recorded and recorded != st.session_state.audio_id:
    st.session_state.audio_id = recorded
    with st.spinner("Onkel Ringo hört zu..."):
        ai_msg = get_response(recorded, ort)
        st.session_state.ringo_chat.append(ai_msg)
        st.rerun()

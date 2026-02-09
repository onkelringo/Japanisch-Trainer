import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- 1. APP CONFIG ---
st.set_page_config(page_title="Onkel Ringos Lernapp", layout="wide")

# --- 2. KANAGAWA DESIGN (Blau, Beige, Rot) ---
st.markdown("""
<style>
    .stApp { background-color: #f4e7d3 !important; color: #002b5b !important; }
    .main .block-container { max-width: 750px !important; margin: auto; }
    h1 { 
        color: #002b5b !important; 
        font-family: 'Georgia', serif;
        border-bottom: 5px solid #bc002d !important; 
        padding-bottom: 10px !important;
    }
    .seller-box { 
        font-size: 1.4rem !important; 
        color: #ffffff !important; 
        background-color: #002b5b !important; 
        padding: 25px !important; 
        border-radius: 0px 30px 0px 30px !important; 
        border-left: 15px solid #bc002d !important;
        margin: 20px 0 !important;
    }
    div[data-testid="stVerticalBlock"] > div:has(svg) {
        display: flex !important; justify-content: center !important; 
        transform: scale(2.5); margin: 60px 0 !important;
    }
    svg { fill: #bc002d !important; }
    section[data-testid="stSidebar"] { 
        background-color: #002b5b !important; 
        border-right: 3px solid #bc002d !important; 
    }
    section[data-testid="stSidebar"] * { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. DYNAMISCHER MODELL-SCAN ---
API_KEY = st.secrets.get("GEMINI_API_KEY")

@st.cache_resource
def get_any_working_model(key):
    if not key: return None
    try:
        genai.configure(api_key=key)
        # Scannt alle Modelle, die Content generieren können
        available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # Bevorzugte Modelle in Reihenfolge
        for pref in ['models/gemini-1.5-flash', 'models/gemini-1.5-pro', 'models/gemini-pro']:
            if pref in available:
                return genai.GenerativeModel(pref)
        
        # Fallback: Nimm einfach das allererste verfügbare
        if available:
            return genai.GenerativeModel(available[0])
        return None
    except:
        return None

if "chat" not in st.session_state: st.session_state.chat = []
if "last_audio_id" not in st.session_state: st.session_state.last_audio_id = None

def get_rollenspiel_antwort(audio_bytes, location):
    model = get_any_working_model(API_KEY)
    if not model: 
        return "FEHLER: Dein API-Key erlaubt derzeit keinen Zugriff auf Gemini-Modelle. Prüfe deinen Plan im Google AI Studio."
    try:
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        prompt = (f"Du bist eine japanische Verkäuferin in {location}. Stefan ist dein Kunde. "
                  "Führe ein echtes Rollenspiel: Antworte höflich und stelle IMMER eine Gegenfrage. "
                  "FORMAT: STEFAN: [Was er sagte] JAPANISCH: [Antwort + Frage] DEUTSCH: [Übersetzung]")
        res = model.generate_content([prompt, audio_part])
        return res.text
    except Exception as e:
        return f"Fehler: {str(e)}"

# --- 4. UI ---
st.title("🌊 Onkel Ringos Lernapp")

with st.sidebar:
    st.markdown("### 📍 Umgebung")
    ort = st.selectbox("Ort:", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus Arima Onsen"])
    if st.button("Reset"):
        st.session_state.chat = []
        st.session_state.last_audio_id = None
        st.rerun()

# Verlauf
for i, msg in enumerate(st.session_state.chat):
    st.divider()
    parts = {"s": "", "j": ""}
    if "STEFAN:" in msg and "JAPANISCH:" in msg:
        parts["s"] = msg.split("STEFAN:").split("JAPANISCH:").strip()
        parts["japan"] = msg.split("JAPANISCH:").split("DEUTSCH:").strip()
    else:
        parts["japan"] = msg

    if parts.get("s"):
        st.write(f"👂 *Onkel Ringo hörte:* {parts['s']}")

    if parts.get("japan"):
        try:
            tts = gTTS(text=parts["japan"], lang='ja')
            b = io.BytesIO(); tts.write_to_fp(b)
            b64 = base64.b64encode(b.getvalue()).decode()
            auto = "autoplay" if i == len(st.session_state.chat)-1 else ""
            st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls {auto}></audio>', unsafe_allow_html=True)
        except: pass

    with st.expander("👁️ Text & Lösung"):
        st.markdown(f'<div class="seller-box">{msg}</div>', unsafe_allow_html=True)

# Mikrofon
st.write("---")
rec_audio = audio_recorder(text="", pause_threshold=3.0, key="mic_final_v28")

if rec_audio and rec_audio != st.session_state.last_audio_id:
    st.session_state.last_audio_id = rec_audio
    with st.spinner("Onkel Ringo wertet aus..."):
        ai_msg = get_rollenspiel_antwort(rec_audio, ort)
        st.session_state.chat.append(ai_msg)
        st.rerun()

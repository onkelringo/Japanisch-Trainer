import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- 1. APP CONFIG ---
st.set_page_config(page_title="Onkel Ringos Lernapp", layout="wide")

# --- 2. KANAGAWA DESIGN ---
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
    .stefan-info { font-size: 0.95rem !important; color: #5a5a5a !important; font-style: italic; }
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
    audio { border: 2px solid #002b5b; border-radius: 10px; width: 100%; }
</style>
""", unsafe_allow_html=True)

# --- 3. INTELLIGENTE MODELL-FINDUNG (FIX FÜR 404) ---
API_KEY = st.secrets.get("GEMINI_API_KEY")

@st.cache_resource
def get_working_model(key):
    if not key: return None
    genai.configure(api_key=key)
    # Liste der möglichen Bezeichnungen für das stabile Flash-Modell
    model_candidates = [
        'gemini-1.5-flash', 
        'models/gemini-1.5-flash', 
        'gemini-1.5-flash-latest',
        'gemini-pro'
    ]
    
    for name in model_candidates:
        try:
            model = genai.GenerativeModel(name)
            # Kleiner Test-Aufruf um Gültigkeit zu prüfen
            model.generate_content("Hi", generation_config={"max_output_tokens": 1})
            return model
        except:
            continue
    return None

if "chat" not in st.session_state: st.session_state.chat = []
if "last_audio_id" not in st.session_state: st.session_state.last_audio_id = None

def get_rollenspiel_antwort(audio_bytes, location):
    model = get_working_model(API_KEY)
    if not model: return "Fehler: Kein Modell (z.B. gemini-1.5-flash) unter deinem API-Key gefunden."
    try:
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        prompt = (f"Du bist eine japanische Verkäuferin in {location}. Stefan ist Kunde. "
                  "Verhalte dich absolut echt: Sei höflich, reagiere auf ihn und stelle IMMER eine "
                  "Gegenfrage (Menge, Tüte, Bezahlung). "
                  "FORMAT: STEFAN: [Transkript] JAPANISCH: [Antwort + Frage] DEUTSCH: [Übersetzung]")
        res = model.generate_content([prompt, audio_part])
        return res.text
    except Exception as e:
        if "429" in str(e): return "Limit erreicht (429). Bitte 60 Sek. warten."
        return f"Fehler: {str(e)}"

# --- 4. UI ---
st.title("🌊 Onkel Ringos Lernapp")

with st.sidebar:
    st.markdown("### 🗺️ Reiseziel")
    ort = st.selectbox("Ort:", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus Arima Onsen"])
    if st.button("Gespräch löschen"):
        st.session_state.chat = []
        st.session_state.last_audio_id = None
        st.rerun()

# Chat-Anzeige
for i, msg in enumerate(st.session_state.chat):
    st.divider()
    parts = {"s": "", "j": ""}
    if "STEFAN:" in msg and "JAPANISCH:" in msg:
        parts["s"] = msg.split("STEFAN:")[1].split("JAPANISCH:")[0].strip()
        parts["j"] = msg.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip()

    if parts["s"]:
        st.markdown(f'<div class="stefan-info">Verstanden: "{parts["s"]}"</div>', unsafe_allow_html=True)

    if parts["j"]:
        try:
            tts = gTTS(text=parts["j"], lang='ja')
            audio_io = io.BytesIO()
            tts.write_to_fp(audio_io)
            b64 = base64.b64encode(audio_io.getvalue()).decode()
            auto = "autoplay" if i == len(st.session_state.chat)-1 else ""
            st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls {auto}></audio>', unsafe_allow_html=True)
        except: pass

    with st.expander("👁️ Text & Lösung"):
        st.markdown(f'<div class="seller-box">{msg}</div>', unsafe_allow_html=True)

# Mikrofon
st.write("---")
st.write("### 🎤 Deine Antwort (Sprechen):")
rec_audio = audio_recorder(text="", icon_size="3x", pause_threshold=3.0, key="mic_v27_final")

if rec_audio and rec_audio != st.session_state.last_audio_id:
    st.session_state.last_audio_id = rec_audio
    with st.spinner("Antwort kommt..."):
        ai_msg = get_rollenspiel_antwort(rec_audio, ort)
        st.session_state.chat.append(ai_msg)
        st.rerun()

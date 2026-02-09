import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- 1. INITIALISIERUNG ---
st.set_page_config(page_title="Onkel Ringos Lernapp", layout="wide")

# --- 2. KANAGAWA DESIGN (Blau, Beige, Rot) ---
st.markdown("""
<style>
    .stApp { background-color: #f4e7d3 !important; }
    .main .block-container { max-width: 700px !important; margin: auto; }
    h1 { color: #002b5b !important; border-bottom: 5px solid #bc002d !important; padding-bottom: 10px; }
    
    .seller-bubble { 
        font-size: 1.4rem !important; color: #ffffff !important; 
        background-color: #002b5b !important; padding: 20px; 
        border-radius: 0 20px 20px 20px; border-left: 10px solid #bc002d;
        margin: 15px 0; box-shadow: 4px 4px 10px rgba(0,0,0,0.2);
    }
    
    .stefan-text { font-size: 0.9rem; color: #5a5a5a; font-style: italic; }

    /* Mikrofon: Die rote Sonne */
    div[data-testid="stVerticalBlock"] > div:has(svg) {
        display: flex !important; justify-content: center !important; 
        transform: scale(2.5); margin: 50px 0 !important;
    }
    svg { fill: #bc002d !important; }

    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #002b5b !important; color: white !important; }
    section[data-testid="stSidebar"] * { color: white !important; }
</style>
""", unsafe_allow_html=True)

# --- 3. DYNAMISCHE MODELL-SUCHE (FIX FÜR 404) ---
@st.cache_resource
def get_working_model():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    try:
        # Wir listen alle verfügbaren Modelle auf
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # Wir bevorzugen Flash für Geschwindigkeit
                if "flash" in m.name:
                    return genai.GenerativeModel(m.name)
        # Fallback: Nimm das erste beste Modell
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return genai.GenerativeModel(models[0]) if models else None
    except:
        return None

# --- 4. SESSION STATE ---
if "chat" not in st.session_state: st.session_state.chat = []
if "last_aid" not in st.session_state: st.session_state.last_aid = None

def ask_ai(audio_bytes, ort):
    model = get_working_model()
    if not model: return "Fehler: API-Verbindung fehlgeschlagen."
    try:
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        prompt = (f"Du bist eine japanische Verkäuferin in {ort}. Stefan ist Kunde. "
                  "Verhalte dich wie im echten Rollenspiel: Antworte höflich und stelle IMMER eine Gegenfrage. "
                  "FORMAT: STEFAN: [Was er sagte] JAPANISCH: [Antwort + Frage] DEUTSCH: [Übersetzung]")
        # Sende kein History-Objekt um Quota zu sparen (Statuslose Anfrage)
        res = model.generate_content([prompt, audio_part])
        return res.text
    except Exception as e:
        return f"Fehler: {str(e)}"

# --- 5. UI ---
st.title("🌊 Onkel Ringos Lernapp")

with st.sidebar:
    st.write("### 📍 Umgebung")
    place = st.selectbox("Wo bist du?", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus Arima Onsen"])
    if st.button("Reset"):
        st.session_state.chat = []
        st.session_state.last_aid = None
        st.rerun()

# Chat Verlauf
for i, msg in enumerate(st.session_state.chat):
    st.divider()
    parts = {"s": "", "j": ""}
    if "STEFAN:" in msg and "JAPANISCH:" in msg:
        parts["s"] = msg.split("STEFAN:")[1].split("JAPANISCH:")[0].strip()
        parts["j"] = msg.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip()

    if parts["s"]:
        st.markdown(f'<div class="stefan-text">Verstanden: "{parts["s"]}"</div>', unsafe_allow_html=True)

    if parts["j"]:
        try:
            tts = gTTS(text=parts["j"], lang='ja')
            b = io.BytesIO(); tts.write_to_fp(b)
            b64 = base64.b64encode(b.getvalue()).decode()
            auto = "autoplay" if i == len(st.session_state.chat)-1 else ""
            st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls {auto}></audio>', unsafe_allow_html=True)
        except: pass

    with st.expander("👁️ Text anzeigen"):
        st.markdown(f'<div class="seller-bubble">{msg}</div>', unsafe_allow_html=True)

# Mikrofon
st.write("---")
st.write("### 🎤 Sprich jetzt (Rollenspiel):")
audio_data = audio_recorder(text="", icon_size="3x", pause_threshold=3.0, key="mic_v30")

if audio_data and audio_data != st.session_state.last_aid:
    st.session_state.last_aid = audio_data
    with st.spinner("Onkel Ringo hört zu..."):
        answer = ask_ai(audio_data, place)
        st.session_state.chat.append(answer)
        st.rerun()

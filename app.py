import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- 1. APP CONFIG (FINALER NAME) ---
st.set_page_config(page_title="Onkel Ringos Lernapp", layout="wide")

# --- 2. FORCIERTES DESIGN (ROT/WEISS/SCHWARZ) ---
st.markdown("""
    <style>
    /* Hintergrund Weiß, Text Schwarz */
    .stApp { background-color: #ffffff !important; color: #000000 !important; }
    .main .block-container { max-width: 750px !important; padding: 2rem !important; margin: auto; }

    /* Titel in Japan-Rot */
    h1 { color: #bc002d !important; border-bottom: 5px solid #bc002d !important; padding-bottom: 10px !important; }

    /* Die Box der Verkäuferin in Schwarz */
    .seller-box { 
        font-size: 1.4rem !important; 
        color: #ffffff !important; 
        background-color: #000000 !important; 
        padding: 20px !important; 
        border-radius: 0px !important; 
        border-left: 15px solid #bc002d !important;
        margin: 15px 0 !important;
    }

    /* Info-Text für transkribiertes Japanisch */
    .stefan-info { font-size: 0.9rem !important; color: #666666 !important; }

    /* Mikrofon-Button Design */
    div[data-testid="stVerticalBlock"] > div:has(svg) {
        display: flex !important; justify-content: center !important; 
        transform: scale(2.2); margin: 50px 0 !important;
    }
    svg { fill: #bc002d !important; }

    /* Sidebar Design */
    section[data-testid="stSidebar"] { background-color: #f8f9fa !important; border-right: 2px solid #bc002d !important; }
    
    /* Erzwungene Textfarben */
    p, span, label, div { color: #000000 !important; }
    .seller-box div, .seller-box p, .seller-box span { color: #ffffff !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. API & MODELL ---
API_KEY = st.secrets.get("GEMINI_API_KEY")

@st.cache_resource
def load_ringo_model(key):
    if not key: return None
    genai.configure(api_key=key)
    return genai.GenerativeModel('gemini-1.5-flash-8b')

if "chat" not in st.session_state: st.session_state.chat = []
if "last_audio_id" not in st.session_state: st.session_state.last_audio_id = None

def get_ai_response(audio_bytes, location):
    model = load_ringo_model(API_KEY)
    if not model: return "Fehler: API Key fehlt!"
    try:
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        # ROLLENSPIEL PROMPT: Die KI muss Fragen stellen und das Gespräch führen
        prompt = (f"Du bist eine japanische Verkäuferin in {location}. Stefan ist dein Kunde. "
                  "Führe ein realistisches Verkaufsgespräch. Reagiere auf das, was er sagt, "
                  "und stelle ihm dann eine passende Anschlussfrage (z.B. nach der Menge, "
                  "ob er bar zahlt oder eine Tüte braucht). Sei höflich. "
                  "FORMAT: STEFAN: [Was er sagte] JAPANISCH: [Deine Antwort + Frage] DEUTSCH: [Übersetzung]")
        
        # Um das Limit (429) zu vermeiden, senden wir nur die letzten 2 Nachrichten als Kontext
        history = st.session_state.chat[-2:] if st.session_state.chat else []
        res = model.generate_content([prompt, *history, audio_part])
        return res.text
    except Exception as e:
        return f"Quota-Limit! Bitte 1 Minute warten. (Fehler: {str(e)})"

# --- 4. UI ---
st.title("🏯 Onkel Ringos Lernapp")

with st.sidebar:
    st.markdown("### 📍 Rollenspiel-Ort")
    ort = st.selectbox("Wo bist du?", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus Arima Onsen"])
    if st.button("Gespräch neu starten"):
        st.session_state.chat = []
        st.session_state.last_audio_id = None
        st.rerun()

# Verlauf
for i, msg in enumerate(st.session_state.chat):
    st.divider()
    
    parts = {"stefan": "", "japan": ""}
    if "STEFAN:" in msg and "JAPANISCH:" in msg:
        parts["stefan"] = msg.split("STEFAN:").split("JAPANISCH:").strip()
        parts["japan"] = msg.split("JAPANISCH:").split("DEUTSCH:").strip()

    if parts["stefan"]:
        st.markdown(f'<div class="stefan-info">Onkel Ringo verstand: "{parts["stefan"]}"</div>', unsafe_allow_html=True)

    if parts["japan"]:
        try:
            tts = gTTS(text=parts["japan"], lang='ja')
            audio_stream = io.BytesIO()
            tts.write_to_fp(audio_stream)
            b64 = base64.b64encode(audio_stream.getvalue()).decode()
            auto = "autoplay" if i == len(st.session_state.chat)-1 else ""
            st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls {auto}></audio>', unsafe_allow_html=True)
        except: pass

    with st.expander("👁️ Text der Verkäuferin anzeigen"):
        st.markdown(f'<div class="seller-box">{msg}</div>', unsafe_allow_html=True)

# Mikrofon
st.write("---")
recorded_audio = audio_recorder(text="Sprechen...", icon_size="2x", pause_threshold=3.0, key="ringo_v21")

if recorded_audio and recorded_audio != st.session_state.last_audio_id:
    st.session_state.last_audio_id = recorded_audio
    with st.spinner("Onkel Ringo hört zu..."):
        ai_msg = get_ai_response(recorded_audio, ort)
        st.session_state.chat.append(ai_msg)
        st.rerun()

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
    /* Hintergrund: Japanisches Papier (Beige) */
    .stApp { background-color: #f4e7d3 !important; color: #002b5b !important; }
    
    .main .block-container { max-width: 750px !important; margin: auto; }

    /* Titel in Preußischblau mit rotem Akzent */
    h1 { 
        color: #002b5b !important; 
        font-family: 'Georgia', serif;
        border-bottom: 5px solid #bc002d !important; 
        padding-bottom: 10px !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }

    /* Die Box der Verkäuferin (Tiefblau der Welle) */
    .seller-box { 
        font-size: 1.4rem !important; 
        color: #ffffff !important; 
        background-color: #002b5b !important; 
        padding: 25px !important; 
        border-radius: 0px 30px 0px 30px !important; 
        border-left: 15px solid #bc002d !important;
        margin: 20px 0 !important;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.2);
    }

    /* Deine Transkription */
    .stefan-info { font-size: 0.95rem !important; color: #5a5a5a !important; font-style: italic; }

    /* Mikrofon: Das Rot der Sonne */
    div[data-testid="stVerticalBlock"] > div:has(svg) {
        display: flex !important; justify-content: center !important; 
        transform: scale(2.5); margin: 60px 0 !important;
    }
    svg { fill: #bc002d !important; }

    /* Sidebar Design */
    section[data-testid="stSidebar"] { 
        background-color: #002b5b !important; 
        border-right: 3px solid #bc002d !important; 
    }
    section[data-testid="stSidebar"] * { color: #ffffff !important; }
    
    /* Audio Player Styling */
    audio { border: 2px solid #002b5b; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 3. API & MODELL-WAHL (LIMIT-UMGEHUNG) ---
API_KEY = st.secrets.get("GEMINI_API_KEY")

@st.cache_resource
def load_stable_model(key):
    if not key: return None
    genai.configure(api_key=key)
    # Wir nehmen EXPLIZIT 1.5-Flash für höhere Free-Tier Quoten
    return genai.GenerativeModel('gemini-1.5-flash')

if "chat" not in st.session_state: st.session_state.chat = []
if "last_audio_id" not in st.session_state: st.session_state.last_audio_id = None

def get_rollenspiel_antwort(audio_bytes, location):
    model = load_stable_model(API_KEY)
    if not model: return "Key fehlt!"
    try:
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        # Rollenspiel-Anweisung
        prompt = (f"Du bist eine japanische Verkäuferin in {location}. Stefan ist Kunde. "
                  "Verhalte dich absolut echt: Sei höflich, reagiere auf ihn und stelle IMMER eine "
                  "Gegenfrage (Menge, Tüte, Bezahlung). "
                  "FORMAT:\nSTEFAN: [Was er sagte]\nJAPANISCH: [Deine Antwort + Frage]\nDEUTSCH: [Übersetzung]")
        
        # KEIN Verlauf senden um Token-Limits pro Minute zu sparen
        res = model.generate_content([prompt, audio_part])
        return res.text
    except Exception as e:
        if "429" in str(e):
            return "LIMIT: Bitte 60 Sek. warten. Google Free Plan braucht eine kurze Pause."
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

# Verlauf (Chronologisch nach unten)
for i, msg in enumerate(st.session_state.chat):
    st.divider()
    
    parts = {"s": "", "j": ""}
    if "STEFAN:" in msg and "JAPANISCH:" in msg:
        parts["s"] = msg.split("STEFAN:").split("JAPANISCH:").strip()
        parts["j"] = msg.split("JAPANISCH:").split("DEUTSCH:").strip()

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
rec_audio = audio_recorder(text="", icon_size="3x", pause_threshold=3.0, key="mic_kanagawa")

if rec_audio and rec_audio != st.session_state.last_audio_id:
    st.session_state.last_audio_id = rec_audio
    with st.spinner("Verkäuferin antwortet..."):
        ai_msg = get_rollenspiel_antwort(rec_audio, ort)
        st.session_state.chat.append(ai_msg)
        st.rerun()

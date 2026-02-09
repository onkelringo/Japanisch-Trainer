import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- API SETUP ---
API_KEY = st.secrets.get("GEMINI_API_KEY")

# --- RADIKALES DESIGN (FLAGGE & LAYOUT) ---
st.set_page_config(page_title="Onkel Ringos Lernapp", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .main .block-container { max-width: 700px; padding: 1rem; margin: auto; }
    
    /* Stefan's Box: Klein und dezent */
    .stefan-box { font-size: 0.85rem; color: #888; margin: 5px 0; }
    
    /* Antwort-Box */
    .seller-box { 
        font-size: 1.3rem !important; color: #00ffcc; background: #1a1c23; 
        padding: 15px; border-radius: 10px; border-left: 5px solid #bc002d;
    }

    /* KYOKUJITSU-KI (Strahlen-Flagge) als Aufnahme-Button */
    /* Wir erzwingen das Design über den Container des Recorders */
    [data-testid="stVerticalBlock"] div:has(svg) {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        transform: scale(2.5);
        margin: 50px auto !important;
        width: 80px !important;
        height: 80px !important;
        border-radius: 50% !important;
        border: 2px solid #bc002d !important;
        box-shadow: 0 0 25px rgba(188, 0, 45, 0.6) !important;
        background: conic-gradient(
            from 0deg,
            #bc002d 0deg 11.25deg, #ffffff 11.25deg 22.5deg,
            #bc002d 22.5deg 33.75deg, #ffffff 33.75deg 45deg,
            #bc002d 45deg 56.25deg, #ffffff 56.25deg 67.5deg,
            #bc002d 67.5deg 78.75deg, #ffffff 78.75deg 90deg,
            #bc002d 90deg 101.25deg, #ffffff 101.25deg 112.5deg,
            #bc002d 112.5deg 123.75deg, #ffffff 123.75deg 135deg,
            #bc002d 135deg 146.25deg, #ffffff 146.25deg 157.5deg,
            #bc002d 157.5deg 168.75deg, #ffffff 168.75deg 180deg,
            #bc002d 180deg 191.25deg, #ffffff 191.25deg 202.5deg,
            #bc002d 202.5deg 213.75deg, #ffffff 213.75deg 225deg,
            #bc002d 225deg 236.25deg, #ffffff 236.25deg 247.5deg,
            #bc002d 247.5deg 258.75deg, #ffffff 258.75deg 270deg,
            #bc002d 270deg 281.25deg, #ffffff 281.25deg 292.5deg,
            #bc002d 292.5deg 303.75deg, #ffffff 303.75deg 315deg,
            #bc002d 315deg 326.25deg, #ffffff 326.25deg 337.5deg,
            #bc002d 337.5deg 348.75deg, #ffffff 348.75deg 360deg
        ) !important;
    }
    
    /* Icon-Farbe anpassen */
    svg { fill: #000 !important; }
    </style>
""", unsafe_allow_html=True)

# --- MODEL-LOGIK (OPTIMIERT GEGEN LIMITS) ---
@st.cache_resource
def get_model(api_key):
    genai.configure(api_key=api_key)
    # 1.5-flash-8b ist das "kleinste" Modell mit den höchsten freien Limits
    return genai.GenerativeModel('gemini-1.5-flash-8b')

# --- CHAT STATE ---
if "chat" not in st.session_state: st.session_state.chat = []
if "last_audio" not in st.session_state: st.session_state.last_audio = None

def ask_ai(audio_bytes, location):
    model = get_model(API_KEY)
    try:
        audio_info = {"mime_type": "audio/wav", "data": audio_bytes}
        # Kurzer Prompt spart Tokens/Limits
        prompt = (f"Verkäuferin in {location}. Stefan spricht. Antworte höflich, wenig Kansai-Dialekt. "
                  "Format: STEFAN: [Text] JAPANISCH: [Antwort] DEUTSCH: [Text]")
        # WICHTIG: Keine History mitschicken um 429 Fehler zu vermeiden
        res = model.generate_content([prompt, audio_info])
        return res.text
    except Exception as e:
        return f"LIMIT! Bitte 30 Sek warten. ({str(e)})"

# --- UI ---
st.title("🏯 Onkel Ringos Lernapp")

with st.sidebar:
    sit = st.selectbox("Ort:", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus Arima Onsen"])
    if st.button("Verlauf löschen"):
        st.session_state.chat = []
        st.rerun()

# Verlauf (Chronologisch von oben nach unten)
for i, msg in enumerate(st.session_state.chat):
    st.divider()
    
    # Extraktion Stefan vs Japanisch
    parts = {"s": "", "j": ""}
    if "STEFAN:" in msg and "JAPANISCH:" in msg:
        parts["s"] = msg.split("STEFAN:").split("JAPANISCH:").strip()
        parts["j"] = msg.split("JAPANISCH:").split("DEUTSCH:").strip()

    if parts["s"]:
        st.markdown(f'<div class="stefan-box">Stefan sagte: {parts["s"]}</div>', unsafe_allow_html=True)

    if parts["j"]:
        try:
            tts = gTTS(text=parts["j"], lang='ja')
            b = io.BytesIO(); tts.write_to_fp(b)
            b64 = base64.b64encode(b.getvalue()).decode()
            # Nur letzte Nachricht spielt automatisch
            auto = "autoplay" if i == len(st.session_state.chat)-1 else ""
            st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls {auto}></audio>', unsafe_allow_html=True)
        except: pass

    with st.expander("👁️ Lösung anzeigen"):
        st.markdown(f'<div class="seller-box">{msg}</div>', unsafe_allow_html=True)

# Mikrofon am Ende
st.write("---")
# Der Recorder-Button übernimmt durch das CSS das Flaggen-Design
audio_data = audio_recorder(text="", icon_size="2x", pause_threshold=3.0, key="ringo_mic")

if audio_data and audio_data != st.session_state.last_audio:
    st.session_state.last_audio = audio_data
    with st.spinner("Onkel Ringo hört zu..."):
        ans = ask_ai(audio_data, sit)
        st.session_state.chat.append(ans)
        st.rerun()

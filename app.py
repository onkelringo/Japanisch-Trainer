import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- API SETUP ---
API_KEY = st.secrets.get("GEMINI_API_KEY")

# --- DESIGN SETUP (KYOKUJITSU-KI DESIGN) ---
st.set_page_config(page_title="Japan Trainer v15", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    .main .block-container { max-width: 800px; padding: 1rem; margin: auto; }
    
    .stefan-box { font-size: 0.85rem; color: #aaa; margin-top: 10px; padding-left: 5px;}
    
    .seller-box { 
        font-size: 1.3rem !important; color: #00ffcc; background: #1a1c23; 
        padding: 18px; border-radius: 10px; border-left: 5px solid #bc002d;
    }

    /* Kyokujitsu-ki (1940er Stil) für den Record Button */
    div[data-testid="stVerticalBlock"] > div:has(svg) {
        display: flex; justify-content: center; 
        transform: scale(2.5); 
        margin: 50px auto !important;
        background-color: #ffffff !important;
        border-radius: 50% !important;
        width: 80px; height: 80px;
        border: 2px solid #bc002d !important;
        box-shadow: 0 0 25px rgba(188, 0, 45, 0.6);
        
        /* Die Strahlen-Optik per CSS-Gradient */
        background: 
            inline-size 100%,
            conic-gradient(from 0deg, 
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
    
    /* Mikrofon-Icon im Zentrum der Strahlen besser sichtbar machen */
    div[data-testid="stVerticalBlock"] > div:has(svg) svg {
        fill: white !important;
        filter: drop-shadow(0px 0px 2px black);
    }
    </style>
""", unsafe_allow_html=True)

# --- MODEL ---
@st.cache_resource
def get_model(api_key):
    try:
        genai.configure(api_key=api_key)
        # Fix auf 1.5-flash für maximale Quota-Stabilität
        return genai.GenerativeModel('gemini-1.5-flash')
    except: return None

# --- LOGIK ---
if "chat" not in st.session_state: st.session_state.chat = []
if "last_audio_hash" not in st.session_state: st.session_state.last_audio_hash = None

def talk_to_seller(audio_bytes, sit):
    model = get_model(API_KEY)
    if not model: return "API Fehler."
    try:
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        prompt = (f"Du bist Verkäuferin in {sit}. Stefan spricht. "
                  "Sei extrem höflich, nutze nur ganz dezent Kansai-Akzent. "
                  "Transkribiere zuerst Stefans Japanisch/Deutsch. "
                  "FORMAT: STEFAN: [Text] JAPANISCH: [Antwort] DEUTSCH: [Übersetzung]")
        res = model.generate_content([prompt, audio_part])
        return res.text
    except Exception as e:
        if "429" in str(e): return "Limit erreicht. Bitte 1 Min warten."
        return f"Fehler: {str(e)}"

# --- UI ---
st.title("🇯🇵 Japan-Trainer: Ashiya")

with st.sidebar:
    situation = st.selectbox("Ort:", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus Arima Onsen"])
    if st.button("Verlauf löschen"):
        st.session_state.chat = []
        st.session_state.last_audio_hash = None
        st.rerun()

# Verlauf Chronologisch
for i, msg in enumerate(st.session_state.chat):
    st.divider()
    
    stefan_text = ""
    jp_text = ""
    if "STEFAN:" in msg and "JAPANISCH:" in msg:
        stefan_text = msg.split("STEFAN:")[1].split("JAPANISCH:")[0].strip()
        jp_text = msg.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip()

    if stefan_text:
        st.markdown(f'<div class="stefan-box">Stefan: "{stefan_text}"</div>', unsafe_allow_html=True)

    if jp_text:
        try:
            tts = gTTS(text=jp_text, lang='ja')
            b = io.BytesIO(); tts.write_to_fp(b)
            b64 = base64.b64encode(b.getvalue()).decode()
            is_new = (i == len(st.session_state.chat) - 1)
            play_attr = "autoplay" if is_new else ""
            st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls {play_attr}></audio>', unsafe_allow_html=True)
        except: pass

    with st.expander("👁️ Antwort lesen"):
        st.markdown(f'<div class="seller-box">{msg}</div>', unsafe_allow_html=True)

# Mikrofon ganz unten
st.write("---")
audio_data = audio_recorder(text="", pause_threshold=3.0, icon_name="microphone", key="mic_v15")

if audio_data is not None:
    curr_hash = hash(audio_data)
    if st.session_state.last_audio_hash != curr_hash:
        st.session_state.last_audio_hash = current_hash
        with st.spinner("..."):
            answer = talk_to_seller(audio_data, situation)
            st.session_state.chat.append(answer)
            st.rerun()

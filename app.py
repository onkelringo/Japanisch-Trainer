import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- API SETUP ---
API_KEY = st.secrets.get("GEMINI_API_KEY")

# --- DESIGN & LAYOUT ---
st.set_page_config(page_title="Sensei Stefan", layout="centered") # Centered = schmalerer Body

st.markdown("""
    <style>
    .stApp { background-color: #0e1117; }
    /* Stefan's Text (Deine Eingabe) */
    .user-msg { font-size: 0.85rem !important; color: #888; margin-bottom: 20px; text-align: center; }
    /* Verkäuferin Box */
    .seller-box { 
        font-size: 1.6rem !important; color: #00ffcc; background: #1a1c23; 
        padding: 20px; border-radius: 12px; border: 1px solid #333;
    }
    /* Mikrofon-Button Styling */
    div[data-testid="stVerticalBlock"] > div:has(svg) {
        display: flex; justify-content: center; transform: scale(2.8); margin: 50px 0;
    }
    /* Button für iPad */
    .stButton > button { width: 100%; height: 55px; font-size: 1.2rem !important; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

if not API_KEY:
    st.warning("⚠️ Bitte 'GEMINI_API_KEY' in den Streamlit Settings unter 'Secrets' eintragen.")
    st.stop()

# --- LOGIK ---
if "chat" not in st.session_state: st.session_state.chat = []

def talk_to_seller(audio, sit):
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
    res = model.generate_content([
        f"Du bist Verkäuferin bei {sit}. Antworte Stefan (Mathelehrer) kurz und frech. FORMAT: JAPANISCH: [Satz] DEUTSCH: [Übersetzung]",
        {"mime_type": "audio/wav", "data": audio}
    ])
    return res.text

# --- UI ---
st.title("🇯🇵 Sensei Stefan")
sit = st.sidebar.selectbox("Ort:", ["Metzgerei Takezono", "McDonald's Ashiya", "Bus Arima Onsen"])

# Mikrofon (Groß, 5 Sek Pause erlaubt)
audio_data = audio_recorder(text="", icon_size="2x", pause_threshold=5.0)

if audio_data:
    with st.spinner("..."):
        answer = talk_to_seller(audio_data, sit)
        st.session_state.chat.append(answer)

# Nachrichten-Anzeige
for msg in reversed(st.session_state.chat):
    st.markdown('<p class="user-box"><i>Du hast gesprochen...</i></p>', unsafe_allow_html=True)
    
    # Audio-Part isolieren & abspielen
    jp = msg.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip() if "JAPANISCH:" in msg else msg
    tts = gTTS(text=jp, lang='ja')
    b = io.BytesIO(); tts.write_to_fp(b)
    b64 = base64.b64encode(b.getvalue()).decode()
    st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls autoplay></audio>', unsafe_allow_html=True)
    
    # Antwort als Option (Expander)
    with st.expander("👁️ Text anzeigen (Lösung)"):
        st.markdown(f'<div class="seller-box">{msg}</div>', unsafe_allow_html=True)
    st.divider()

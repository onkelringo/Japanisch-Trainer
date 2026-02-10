import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- 1. INITIALISIERUNG ---
st.set_page_config(page_title="Onkel Ringos Japan-Training", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f4e7d3 !important; }
    h1 { color: #002b5b !important; border-bottom: 5px solid #bc002d !important; }
    .seller-bubble { 
        font-size: 1.1rem !important; color: #ffffff !important; 
        background-color: #002b5b !important; padding: 15px; 
        border-radius: 15px; border-left: 8px solid #bc002d;
        margin: 10px 0;
    }
    .stefan-text { font-size: 1rem; color: #bc002d; font-weight: bold; margin-top: 15px; }
    /* Mikrofon-Zentrierung */
    div[data-testid="stVerticalBlock"] > div:has(svg) {
        display: flex !important; justify-content: center !important; 
        transform: scale(1.3); margin: 20px 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. KI MODELL ---
@st.cache_resource
def get_model():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key: return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

# --- 3. SESSION STATE ---
if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "display_history" not in st.session_state: st.session_state.display_history = []
if "last_hash" not in st.session_state: st.session_state.last_hash = None

def ask_ai(audio_bytes, ort):
    model = get_model()
    if not model: return "API Fehler"
    
    system_instruction = (
        f"Du bist eine japanische Verkäuferin in {ort}. Stefan ist Ausländer und lernt Japanisch. "
        "REGELEINHALTUNG: "
        "1. Sei extrem höflich, aber sprich einfaches Japanisch. "
        "2. Antworte in maximal 2 Sätzen. "
        "3. Stelle IMMER genau EINE Frage am Ende. "
        "4. ABLAUF: Begrüßung -> Herkunft -> Bestellung -> 'O-machido-sama' -> Smalltalk (Dauer des Aufenthalts). "
        "FORMAT: STEFAN: [Was er sagte] JAPANISCH: [Antwort + Frage] DEUTSCH: [Übersetzung]"
    )
    
    try:
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        res = model.generate_content([system_instruction] + st.session_state.chat_history[-6:] + [audio_part])
        st.session_state.chat_history.append(res.text)
        return res.text
    except Exception as e:
        return f"Fehler: {str(e)}"

# --- 4. UI ---
st.title("🏯 Rollenspiel: Japanische Verkäuferin")

with st.sidebar:
    place = st.selectbox("Ort:", ["Metzgerei Takezono", "McDonald's", "Busstation Arima Onsen"])
    if st.button("Gespräch Neustarten"):
        st.session_state.chat_history = []
        st.session_state.display_history = []
        st.session_state.last_hash = None
        st.rerun()

# Verlauf anzeigen
for i, entry in enumerate(st.session_state.display_history):
    s_text = "..."
    j_text = ""
    d_text = ""
    
    if "STEFAN:" in entry and "JAPANISCH:" in entry:
        s_text = entry.split("STEFAN:")[1].split("JAPANISCH:")[0].strip()
        j_text = entry.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip()
        d_text = entry.split("DEUTSCH:")[1].strip() if "DEUTSCH:" in entry else ""

    st.markdown(f'<div class="stefan-text">👤 Stefan: „{s_text}“</div>', unsafe_allow_html=True)
    
    if j_text:
        # Audio-Generierung
        tts = gTTS(text=j_text, lang='ja')
        b = io.BytesIO()
        tts.write_to_fp(b)
        b64 = base64.b64encode(b.getvalue()).decode()
        
        # FIX: Autoplay nur für die absolut letzte Nachricht
        is_latest = (i == len(st.session_state.display_history) - 1)
        if is_latest:
            # Wir nutzen HTML5 Audio mit Autoplay und einem Script-Trigger
            audio_html = f"""
                <audio id="japanese_audio" autoplay>
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                <script>
                    var audio = document.getElementById('japanese_audio');
                    audio.play();
                </script>
            """
            st.markdown(audio_html, unsafe_allow_html=True)
        else:
            st.audio(io.BytesIO(base64.b64decode(b64)), format="audio/mp3")

    with st.expander("Übersetzung anzeigen"):
        st.markdown(f'<div class="seller-bubble"><b>JP:</b> {j_text}<br><br><b>DE:</b> {d_text}</div>', unsafe_allow_html=True)

# --- 5. RECORDER ---
st.write("---")
audio_data = audio_recorder(text="Antworten (Klicken)", icon_size="3x", pause_threshold=2.5, key="v4_mic")

if audio_data:
    new_hash = hash(audio_data)
    if st.session_state.last_hash != new_hash:
        st.session_state.last_hash = new_hash
        with st.spinner("Die Dame antwortet..."):
            ans = ask_ai(audio_data, place)
            st.session_state.display_history.append(ans)
            st.rerun()

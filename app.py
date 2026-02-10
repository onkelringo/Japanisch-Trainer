import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64
import re

# --- 1. SETUP & DESIGN (HOHE KONTRASTE) ---
st.set_page_config(page_title="Japanisch Trainer", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #f4e7d3 !important; }
    h1, h2, h3 { color: #002b5b !important; font-weight: 800 !important; }
    p, span, label { color: #1a1a1a !important; font-weight: 500 !important; }
    
    .chat-bubble { 
        background: #ffffff; padding: 20px; border-radius: 15px; 
        border: 2px solid #002b5b; margin: 15px 0;
        box-shadow: 5px 5px 0px #bc002d;
    }
    .jp-text { font-size: 1.4rem; color: #002b5b; font-weight: bold; display: block; margin-bottom: 5px; }
    .de-text { font-size: 1rem; color: #bc002d; font-style: italic; }
    .stefan-box { color: #444; font-weight: bold; border-bottom: 1px solid #ccc; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 2. KI LOGIK ---
@st.cache_resource
def get_model():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key: return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

if "messages" not in st.session_state: st.session_state.messages = []
if "last_hash" not in st.session_state: st.session_state.last_hash = None

def ask_ai(audio_bytes, ort):
    model = get_model()
    # Der Prompt erzwingt jetzt Trenner, die wir sicher finden können
    prompt = (f"Du bist eine japanische Verkäuferin in {ort}. Stefan lernt Japanisch. "
              "Antworte kurz (max. 2 Sätze) auf Japanisch und stelle eine Frage. "
              "Nutze GENAU dieses Format:\n"
              "TRANSKRIPT: [Was Stefan sagte]\n"
              "ANTWORT: [Deine Antwort auf Japanisch]\n"
              "UEBERSETZUNG: [Deutsche Übersetzung]")
    
    try:
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        res = model.generate_content([prompt] + [m["raw"] for m in st.session_state.messages[-3:]] + [audio_part])
        return res.text
    except Exception as e:
        return f"Fehler: {str(e)}"

# --- 3. UI ---
st.title("🌊 Onkel Ringos Japan-Trainer")

with st.sidebar:
    st.markdown("### 📍 Szenario")
    ort = st.selectbox("Wo bist du?", ["Metzgerei Takezono", "McDonald's Ashiya", "Arima Onsen Bus"])
    if st.button("Gespräch löschen"):
        st.session_state.messages = []
        st.session_state.last_hash = None
        st.rerun()

# Verlauf anzeigen
for i, m in enumerate(st.session_state.messages):
    is_latest = (i == len(st.session_state.messages) - 1)
    
    with st.container():
        st.markdown(f'<div class="stefan-box">👤 Stefan: {m["stefan"]}</div>', unsafe_allow_html=True)
        
        # Audio
        try:
            tts = gTTS(text=m['japanisch'], lang='ja')
            b = io.BytesIO(); tts.write_to_fp(b); b64 = base64.b64encode(b.getvalue()).decode()
            if is_latest:
                st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls autoplay></audio>', unsafe_allow_html=True)
            else:
                st.audio(io.BytesIO(base64.b64decode(b64)), format="audio/mp3")
        except: st.error("Audio-Fehler")

        st.markdown(f"""
        <div class="chat-bubble">
            <span class="jp-text">{m['japanisch']}</span>
            <span class="de-text">({m['deutsch']})</span>
        </div>
        """, unsafe_allow_html=True)

# --- 4. MIKROFON (AM ENDE DER SEITE) ---
st.write("---")
st.write("### 🎤 Sprich jetzt:")
# Dynamischer Key verhindert das Einfrieren
audio_data = audio_recorder(text="", icon_size="3x", pause_threshold=2.5, key=f"mic_{len(st.session_state.messages)}")

if audio_data:
    curr_hash = hash(audio_data)
    if st.session_state.last_hash != curr_hash:
        st.session_state.last_hash = curr_hash
        with st.spinner("Höre zu..."):
            raw_res = ask_ai(audio_data, ort)
            
            # Robustes Parsing mit Regex
            s_match = re.search(r"TRANSKRIPT:(.*?)(?=ANTWORT:|$)", raw_res, re.S)
            j_match = re.search(r"ANTWORT:(.*?)(?=UEBERSETZUNG:|$)", raw_res, re.S)
            d_match = re.search(r"UEBERSETZUNG:(.*)", raw_res, re.S)
            
            if j_match:
                st.session_state.messages.append({
                    "stefan": s_match.group(1).strip() if s_match else "...",
                    "japanisch": j_match.group(1).strip(),
                    "deutsch": d_match.group(1).strip() if d_match else "",
                    "raw": raw_res
                })
                st.rerun()
            else:
                st.warning("Die KI hat nicht im richtigen Format geantwortet. Versuch es nochmal!")

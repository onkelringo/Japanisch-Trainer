import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64
import re

# --- 1. SETUP & ROBUSTES DESIGN ---
st.set_page_config(page_title="Japanisch Trainer", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #f4e7d3 !important; }
    h1, h2, h3 { color: #002b5b !important; font-weight: 800 !important; }
    
    .chat-bubble { 
        background: #ffffff; padding: 20px; border-radius: 15px; 
        border: 2px solid #002b5b; margin: 15px 0;
        box-shadow: 4px 4px 0px #bc002d;
    }
    .jp-text { font-size: 1.5rem !important; color: #002b5b !important; font-weight: bold; display: block; }
    .de-text { font-size: 1rem !important; color: #bc002d !important; font-style: italic; margin-top: 10px; display: block; }
    .stefan-box { color: #1a1a1a !important; font-weight: bold; background: rgba(255,255,255,0.5); padding: 5px 10px; border-radius: 5px; }
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
    # Extrem strenger Prompt
    prompt = (f"Du bist eine japanische Verkäuferin in {ort}. Stefan lernt Japanisch.\n"
              "VERHALTENSREGELN:\n"
              "1. Antworte kurz (1-2 Sätze) auf Japanisch.\n"
              "2. Stelle immer EINE Frage.\n"
              "3. Halte dich EXAKT an dieses Schema, ohne Abweichung:\n\n"
              "TRANSKRIPT: [Was Stefan sagte]\n"
              "ANTWORT: [Japanisch]\n"
              "UEBERSETZUNG: [Deutsch]")
    
    try:
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        res = model.generate_content([prompt] + [m["raw"] for m in st.session_state.messages[-3:]] + [audio_part])
        return res.text
    except Exception as e:
        return f"Fehler: {str(e)}"

# --- 3. PARSING LOGIK (DER STABILITÄTS-ANKER) ---
def parse_response(text):
    # Wir suchen nach den Markern, ignorieren aber Groß/Kleinschreibung
    s_match = re.search(r"TRANSKRIPT:(.*?)(?=ANTWORT:|$)", text, re.S | re.I)
    j_match = re.search(r"ANTWORT:(.*?)(?=UEBERSETZUNG:|$)", text, re.S | re.I)
    d_match = re.search(r"UEBERSETZUNG:(.*)", text, re.S | re.I)
    
    stefan = s_match.group(1).strip() if s_match else "Unklar"
    japanisch = j_match.group(1).strip() if j_match else ""
    deutsch = d_match.group(1).strip() if d_match else ""
    
    # Fallback: Falls die KI alles in einen Block haut
    if not japanisch and len(text) > 5:
        # Nimm den Text, der japanische Schriftzeichen enthält
        jp_chars = re.findall(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+.*", text)
        japanisch = jp_chars[0] if jp_chars else text
        deutsch = "Übersetzung nicht im Format"
        
    return stefan, japanisch, deutsch

# --- 4. UI ---
st.title("🏯 Onkel Ringos Japan-Trainer")

with st.sidebar:
    st.markdown("### 📍 Szenario")
    ort = st.selectbox("Ort:", ["Metzgerei Takezono", "McDonald's Ashiya", "Arima Onsen Bus"])
    if st.button("Gespräch löschen"):
        st.session_state.messages = []
        st.session_state.last_hash = None
        st.rerun()

# Verlauf anzeigen
for i, m in enumerate(st.session_state.messages):
    is_latest = (i == len(st.session_state.messages) - 1)
    
    st.markdown(f'<div class="stefan-box">👤 Stefan: {m["stefan"]}</div>', unsafe_allow_html=True)
    
    # Audio-Ausgabe
    if m['japanisch']:
        try:
            tts = gTTS(text=m['japanisch'], lang='ja')
            b = io.BytesIO(); tts.write_to_fp(b); b64 = base64.b64encode(b.getvalue()).decode()
            if is_latest:
                st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls autoplay></audio>', unsafe_allow_html=True)
            else:
                st.audio(io.BytesIO(base64.b64decode(b64)), format="audio/mp3")
        except: pass

    st.markdown(f"""
    <div class="chat-bubble">
        <span class="jp-text">{m['japanisch']}</span>
        <span class="de-text">({m['deutsch']})</span>
    </div>
    """, unsafe_allow_html=True)

# --- 5. MIKROFON ---
st.write("---")
# Der Key sorgt dafür, dass das Mikrofon nach jedem Turn "frisch" ist
audio_data = audio_recorder(text="Aufnahme läuft...", icon_size="3x", pause_threshold=2.5, key=f"mic_{len(st.session_state.messages)}")

if audio_data:
    curr_hash = hash(audio_data)
    if st.session_state.last_hash != curr_hash:
        st.session_state.last_hash = curr_hash
        with st.spinner("Höre zu..."):
            raw_res = ask_ai(audio_data, ort)
            s, j, d = parse_response(raw_res)
            
            if j: # Nur speichern, wenn wir japanischen Text haben
                st.session_state.messages.append({
                    "stefan": s,
                    "japanisch": j,
                    "deutsch": d,
                    "raw": raw_res
                })
                st.rerun()

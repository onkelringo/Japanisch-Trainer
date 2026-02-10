import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64
import re

# --- 1. SETUP ---
st.set_page_config(page_title="Onkel Ringos Japan-Trainer", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #f4e7d3 !important; }
    .stefan-box { background: #e8f0fe; padding: 12px; border-radius: 10px; border-left: 5px solid #002b5b; margin: 10px 0; color: #1a1a1a; }
    .help-box { background: #ffffff; padding: 15px; border-radius: 10px; border: 2px dashed #bc002d; margin-top: 10px; color: #1a1a1a; }
    h1, h2, h3 { color: #002b5b !important; }
    .stAudio { margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 2. MODELL-SUCHE ---
@st.cache_resource
def get_working_model():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key: return None
    genai.configure(api_key=api_key)
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for target in ["models/gemini-1.5-flash-latest", "models/gemini-1.5-flash", "models/gemini-pro"]:
            if target in models: return genai.GenerativeModel(target)
        return genai.GenerativeModel(models[0]) if models else None
    except: return None

# --- 3. SESSION STATE ---
if "chat_history" not in st.session_state:
    # Initialer Begrüßungs-Prompt (Die KI erstellt die erste Nachricht)
    st.session_state.chat_history = []
if "last_hash" not in st.session_state:
    st.session_state.last_hash = None

def get_ai_response(audio_bytes=None, ort="Laden", initial=False):
    model = get_working_model()
    if not model: return "FEHLER: API nicht erreichbar."
    
    system_instruction = (
        f"Du bist eine japanische Verkäuferin in {ort}. Stefan lernt Japanisch. "
        "REGLER: Antworte kurz (1-2 Sätze) + 1 Frage. Format strikt einhalten:\n"
        "STEFAN_DE: [Was er sagte auf Deutsch]\n"
        "ANTWORT_JP: [Japanisch]\n"
        "ANTWORT_DE: [Deutsch]\n"
        "ROMAJI: [Lautschrift]"
    )

    try:
        if initial:
            res = model.generate_content(f"{system_instruction}\n\nBegrüße Stefan herzlich im Laden und frage ihn etwas Einfaches.")
        else:
            audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
            res = model.generate_content([system_instruction] + st.session_state.chat_history[-4:] + [audio_part])
        return res.text
    except Exception as e:
        return f"FEHLER: {str(e)}"

# --- 4. UI ---
st.title("🏯 Japanisch Sprech-Training")

with st.sidebar:
    ort = st.selectbox("Szenario:", ["Metzgerei Takezono", "McDonald's", "Busstation Arima Onsen"])
    if st.button("Gespräch Neustarten"):
        st.session_state.chat_history = []
        st.session_state.last_hash = None
        st.rerun()

# Automatischer Start der Begrüßung
if not st.session_state.chat_history:
    with st.spinner("Verkäuferin macht den Laden bereit..."):
        first_msg = get_ai_response(ort=ort, initial=True)
        st.session_state.chat_history.append(first_msg)

# Verlauf anzeigen
for i, m in enumerate(st.session_state.chat_history):
    # Robustes Parsing
    s_de = re.search(r"STEFAN_DE:(.*?)(?=ANTWORT_JP:|$)", m, re.S | re.I)
    a_jp = re.search(r"ANTWORT_JP:(.*?)(?=ANTWORT_DE:|$)", m, re.S | re.I)
    a_de = re.search(r"ANTWORT_DE:(.*?)(?=ROMAJI:|$)", m, re.S | re.I)
    romaji = re.search(r"ROMAJI:(.*)", m, re.S | re.I)

    if a_jp:
        jp_text = a_jp.group(1).strip()
        
        # 1. Stefans Part (nur zeigen wenn vorhanden, also nicht bei der ersten Begrüßung)
        if s_de and len(s_de.group(1).strip()) > 1:
            st.markdown(f'<div class="stefan-box"><b>Stefan (übersetzt):</b> {s_de.group(1).strip()}</div>', unsafe_allow_html=True)
        
        # 2. Audio Verkäuferin
        try:
            tts = gTTS(text=jp_text, lang='ja')
            b = io.BytesIO(); tts.write_to_fp(b); b64 = base64.b64encode(b.getvalue()).decode()
            is_latest = (i == len(st.session_state.chat_history) - 1)
            
            st.write(f"📢 **Verkäuferin:**")
            if is_latest:
                st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls autoplay></audio>', unsafe_allow_html=True)
            else:
                st.audio(io.BytesIO(base64.b64decode(b64)), format="audio/mp3")
        except: st.error("Audio-Fehler")

        # 3. Hilfe
        with st.expander("Texthilfe (Japanisch / Romaji / Deutsch)"):
            st.markdown(f"""
            <div class="help-box">
                <b>JP:</b> {jp_text}<br>
                <b>RJ:</b> {romaji.group(1).strip() if romaji else "---"}<br>
                <b>DE:</b> {a_de.group(1).strip() if a_de else "---"}
            </div>
            """, unsafe_allow_html=True)
        st.divider()

# --- 5. RECORDER ---
st.write("### 🎤 Deine Antwort:")
audio_data = audio_recorder(text="", icon_size="3x", pause_threshold=2.5, key=f"mic_{len(st.session_state.chat_history)}")

if audio_data:
    curr_hash = hash(audio_data)
    if st.session_state.last_hash != curr_hash:
        st.session_state.last_hash = curr_hash
        with st.spinner("Höre zu..."):
            res = get_ai_response(audio_bytes=audio_data, ort=ort)
            if res:
                st.session_state.chat_history.append(res)
                st.rerun()


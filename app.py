import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64
import re

# --- 1. SETUP ---
st.set_page_config(page_title="Japanisch-Trainer", layout="centered")

st.markdown("""
<style>
    .stApp { background-color: #f4e7d3 !important; }
    .stefan-box { background: white; padding: 15px; border-radius: 10px; border-left: 5px solid #002b5b; margin: 10px 0; color: #1a1a1a; }
    .help-box { background: #ffffff; padding: 15px; border-radius: 10px; border: 2px dashed #bc002d; margin-top: 10px; color: #1a1a1a; }
    h1, h2, h3 { color: #002b5b !important; }
</style>
""", unsafe_allow_html=True)

# --- 2. DYNAMISCHE MODELL-SUCHE (FIX FÜR 404) ---
@st.cache_resource
def get_working_model():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        st.error("API Key fehlt!")
        return None
    genai.configure(api_key=api_key)
    try:
        # Wir suchen das beste verfügbare Modell auf deinem Account
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Priorität: Flash 1.5 -> Flash 1.0 -> Pro 1.5 -> Irgendeins
        target_models = ["models/gemini-1.5-flash-latest", "models/gemini-1.5-flash", "models/gemini-pro"]
        
        for tm in target_models:
            if tm in available_models:
                return genai.GenerativeModel(tm)
        
        return genai.GenerativeModel(available_models[0]) if available_models else None
    except Exception as e:
        st.error(f"Modell-Suche fehlgeschlagen: {e}")
        return None

if "chat_history" not in st.session_state: st.session_state.chat_history = []
if "last_hash" not in st.session_state: st.session_state.last_hash = None

def run_conversation(audio_bytes, ort):
    model = get_working_model()
    if not model: return None
    
    prompt = (f"Du bist eine japanische Verkäuferin in {ort}. "
              "Verarbeite Stefans Audio-Input und antworte IMMER in diesem Format:\n"
              "STEFAN_DE: [Deutsche Übersetzung von dem, was Stefan auf Japanisch gesagt hat]\n"
              "ANTWORT_JP: [Deine Antwort auf Japanisch, max. 2 Sätze]\n"
              "ANTWORT_DE: [Deutsche Übersetzung deiner Antwort]\n"
              "ROMAJI: [Deine Antwort in Lautschrift]")
    
    try:
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        # Kontext-Management: Nur die letzten 4 Nachrichten mitsenden
        context = st.session_state.chat_history[-4:]
        res = model.generate_content([prompt] + context + [audio_part])
        return res.text
    except Exception as e:
        st.error(f"KI Fehler: {e}")
        return None

# --- 3. UI ---
st.title("🏯 Japanisch Sprech-Training")

with st.sidebar:
    ort = st.selectbox("Szenario:", ["Metzgerei Takezono", "McDonald's", "Busstation Arima Onsen"])
    if st.button("Gespräch löschen"):
        st.session_state.chat_history = []
        st.session_state.last_hash = None
        st.rerun()

# Verlauf anzeigen
for i, m in enumerate(st.session_state.chat_history):
    text = m if isinstance(m, str) else ""
    # Robuste Suche mit Regex
    s_de = re.search(r"STEFAN_DE:(.*?)(?=ANTWORT_JP:|$)", text, re.S | re.I)
    a_jp = re.search(r"ANTWORT_JP:(.*?)(?=ANTWORT_DE:|$)", text, re.S | re.I)
    a_de = re.search(r"ANTWORT_DE:(.*?)(?=ROMAJI:|$)", text, re.S | re.I)
    romaji = re.search(r"ROMAJI:(.*)", text, re.S | re.I)

    if a_jp:
        with st.container():
            # 1. Was Stefan gesagt hat (Übersetzung zur Kontrolle)
            st.markdown(f'<div class="stefan-box"><b>Du sagtest (Deutsch übersetzt):</b><br>{s_de.group(1).strip() if s_de else "Habe dich leider nicht verstanden."}</div>', unsafe_allow_html=True)
            
            # 2. Audio der Verkäuferin
            jp_text = a_jp.group(1).strip()
            try:
                tts = gTTS(text=jp_text, lang='ja')
                b = io.BytesIO(); tts.write_to_fp(b); b64 = base64.b64encode(b.getvalue()).decode()
                
                is_latest = (i == len(st.session_state.chat_history) - 1)
                st.write("📢 **Antwort der Verkäuferin:**")
                if is_latest:
                    st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls autoplay></audio>', unsafe_allow_html=True)
                else:
                    st.audio(io.BytesIO(base64.b64decode(b64)), format="audio/mp3")
            except:
                st.warning("Audio konnte nicht generiert werden.")

            # 3. Hilfe-Button (Texte erst auf Klick)
            with st.expander("Hilfe: Japanischen Text & Romaji einblenden"):
                st.markdown(f"""
                <div class="help-box">
                    <b>Japanisch:</b> {jp_text}<br><br>
                    <b>Romaji:</b> {romaji.group(1).strip() if romaji else "---"}<br><br>
                    <b>Deutsch:</b> {a_de.group(1).strip() if a_de else "---"}
                </div>
                """, unsafe_allow_html=True)
        st.divider()

# --- 4. AUFNAHME ---
st.write("### 🎤 Sprich jetzt auf Japanisch:")
# Dynamischer Key verhindert Recorder-Hänger
audio_data = audio_recorder(text="", icon_size="3x", pause_threshold=2.5, key=f"mic_{len(st.session_state.chat_history)}")

if audio_data:
    curr_hash = hash(audio_data)
    if st.session_state.last_hash != curr_hash:
        st.session_state.last_hash = curr_hash
        with st.spinner("Die Verkäuferin hört zu..."):
            response_text = run_conversation(audio_data, ort)
            if response_text:
                st.session_state.chat_history.append(response_text)
                st.rerun()

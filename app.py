import streamlit as st
import google.generativeai as genai
from audio_recorder_streamlit import audio_recorder
from gtts import gTTS
import io
import base64

# --- 1. KONFIGURATION ---
st.set_page_config(page_title="Japanisch-Trainer", layout="centered")

# Design: Fokus auf das Gespräch
st.markdown("""
<style>
    .stApp { background-color: #fdf6e3; }
    .chat-card { 
        background: white; padding: 15px; border-radius: 10px; 
        border-left: 5px solid #bc002d; margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .japanese-text { font-size: 1.2rem; color: #002b5b; font-weight: bold; }
    .german-sub { font-size: 0.9rem; color: #666; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# --- 2. KI LOGIK ---
@st.cache_resource
def load_model():
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key: return None
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_hash" not in st.session_state:
    st.session_state.last_hash = None

def process_audio(audio_bytes, ort):
    model = load_model()
    prompt = (
        f"Du bist eine japanische Verkäuferin in {ort}. Stefan lernt Japanisch. "
        "REGLER: Antworte NUR auf Japanisch (höflich, einfach, max 2 Sätze). "
        "Stelle immer eine Anschlussfrage. "
        "Antworte STRENG in diesem Schema:\n"
        "STEFAN: [Was er sagte]\n"
        "JAPANISCH: [Deine Antwort]\n"
        "DEUTSCH: [Übersetzung deiner Antwort]"
    )
    
    try:
        audio_part = {"mime_type": "audio/wav", "data": audio_bytes}
        # Kontext mitgeben
        history = [m["raw"] for m in st.session_state.messages[-4:]]
        response = model.generate_content([prompt] + history + [audio_part])
        return response.text
    except Exception as e:
        return f"Fehler: {str(e)}"

# --- 3. UI ---
st.title("🏯 Japanisch Hör-Sprech-Trainer")
st.write(f"Übe dein Japanisch im Rollenspiel.")

with st.sidebar:
    ort = st.selectbox("Szenario:", ["Metzgerei Takezono", "McDonald's Ashiya", "Arima Onsen Bus"])
    if st.button("Gespräch löschen"):
        st.session_state.messages = []
        st.session_state.last_hash = None
        st.rerun()

# Anzeige des Verlaufs
for i, m in enumerate(st.session_state.messages):
    is_latest = (i == len(st.session_state.messages) - 1)
    
    with st.container():
        st.markdown(f"**Stefan:** {m['stefan']}")
        
        # Audio-Ausgabe (Japanisch)
        tts = gTTS(text=m['japanisch'], lang='ja')
        b = io.BytesIO(); tts.write_to_fp(b); b64 = base64.b64encode(b.getvalue()).decode()
        
        if is_latest:
            st.markdown(f'<audio src="data:audio/mp3;base64,{b64}" controls autoplay></audio>', unsafe_allow_html=True)
        else:
            st.audio(io.BytesIO(base64.b64decode(b64)), format="audio/mp3")
            
        with st.expander("Hilfe / Text anzeigen"):
            st.markdown(f"""
            <div class="chat-card">
                <div class="japanese-text">{m['japanisch']}</div>
                <div class="german-sub">{m['deutsch']}</div>
            </div>
            """, unsafe_allow_html=True)

# --- 4. AUFNAHME ---
st.write("---")
# Der Key ändert sich mit der Anzahl der Nachrichten -> erzwingt Refresh des Recorders
audio_data = audio_recorder(
    text="Sprich jetzt auf Japanisch...", 
    icon_size="3x", 
    pause_threshold=2.5, 
    key=f"rec_{len(st.session_state.messages)}"
)

if audio_data:
    curr_hash = hash(audio_data)
    if st.session_state.last_hash != curr_hash:
        st.session_state.last_hash = curr_hash
        with st.spinner("Verkäuferin hört zu..."):
            raw_res = process_audio(audio_data, ort)
            
            # Parsen der Antwort
            try:
                s_text = raw_res.split("STEFAN:")[1].split("JAPANISCH:")[0].strip()
                j_text = raw_res.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip()
                d_text = raw_res.split("DEUTSCH:")[1].strip()
                
                st.session_state.messages.append({
                    "stefan": s_text,
                    "japanisch": j_text,
                    "deutsch": d_text,
                    "raw": raw_res
                })
                st.rerun()
            except:
                st.error("Die KI hat das Format nicht eingehalten. Bitte versuch es noch einmal.")

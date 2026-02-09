import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import io
import base64

# --- BUNTES IPAD PRO DESIGN ---
st.set_page_config(page_title="Sensei Stefans Japan-Coach", layout="wide")

st.markdown("""
    <style>
    /* Hintergrund & Farbverlauf */
    .stApp {
        background: linear-gradient(135deg, #1e1e2f 0%, #2d1b33 100%);
        color: #ffffff;
    }

    /* Boxen für Chat-Nachrichten */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.05) !important;
        border-radius: 15px !important;
        border: 1px solid #ff4b4b !important;
        margin-bottom: 10px;
    }

    /* XXL Schrift für Stefan */
    .stMarkdown p {
        font-size: 1.5rem !important;
        line-height: 1.6;
        color: #f0f0f0;
    }

    /* Der "Frech-Faktor" Header */
    h1 {
        color: #ff4b4b !important;
        text-shadow: 2px 2px #5d00ff;
        font-size: 3rem !important;
    }

    /* Audio Player Styling */
    audio {
        width: 100%;
        filter: invert(100%) hue-rotate(180deg) brightness(1.5);
        height: 50px;
    }

    /* Input-Feld Kontrast */
    .stChatInput input {
        background-color: #262730 !important;
        color: white !important;
        border: 2px solid #5d00ff !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- INTELLIGENTE MODELL-SUCHE ---
@st.cache_resource
def get_best_model(api_key):
    genai.configure(api_key=api_key)
    try:
        models = genai.list_models()
        # Suche nach Pro-Modellen, dann Flash, dann alles andere
        model_names = [m.name for m in models if 'generateContent' in m.supported_generation_methods]

        # Prioritätenliste
        for preferred in ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]:
            for m in model_names:
                if preferred in m:
                    return m
        return model_names[0] if model_names else None
    except Exception as e:
        return None

# --- AUDIO LOGIK ---
def generate_audio_html(text):
    try:
        # Extraktion des japanischen Teils
        if "JAPANISCH:" in text:
            jp_part = text.split("JAPANISCH:")[1].split("DEUTSCH:")[0].strip()
        else:
            jp_part = text

        tts = gTTS(text=jp_part, lang='ja')
        audio_io = io.BytesIO()
        tts.write_to_fp(audio_io)
        b64 = base64.b64encode(audio_io.getvalue()).decode()
        return f'<audio controls autoplay src="data:audio/mp3;base64,{b64}"></audio>'
    except:
        return None

# --- APP START ---
st.title("⛩️ Sensei Stefan: Tokyo Nights")

with st.sidebar:
    st.header("Konfiguration")
    api_key = st.text_input("Dein Gemini Key", type="password")

    if api_key:
        model_id = get_best_model(api_key)
        if model_id:
            st.success(f"Aktiv: {model_id}")
        else:
            st.error("Kein Modell gefunden.")

    st.divider()
    location = st.selectbox(
        "Wo bist du heute?",
        ["Wähle dein Abenteuer...", "Metzgerei Takezono", "McDonald's Ashiya", "Bus nach Arima Onsen"]
    )

if not api_key or location == "Wähle dein Abenteuer...":
    st.info("👋 Hallo Stefan! Gib links den Key ein und wähle einen Ort, um das Training zu starten.")
    st.stop()

# --- CHAT STATE ---
if "messages" not in st.session_state or st.session_state.get("last_loc") != location:
    st.session_state.messages = []
    st.session_state.last_loc = location

    # Der freche Start-Prompt
    model = genai.GenerativeModel(model_id)
    intro_prompt = (
        f"Du bist ein extrem höflicher, aber leicht sarkastischer Angestellter bei {location}. "
        "Stefan (48, Mathelehrer aus Deutschland) kommt zu dir. Er lernt Japanisch. "
        "Begrüße ihn formell, aber mach eine kleine Bemerkung darüber, dass Japanisch lernen "
        "schwerer ist als Kurvendiskussionen. Antworte nur im Format:\n"
        "JAPANISCH: [Satz]\nDEUTSCH: [Übersetzung]"
    )
    try:
        response = model.generate_content(intro_prompt)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
    except:
        st.error("API-Limit erreicht oder Fehler.")

# --- DISPLAY ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])
        if msg["role"] == "assistant" and msg == st.session_state.messages[-1]:
            audio_html = generate_audio_html(msg["content"])
            if audio_html:
                st.markdown(audio_html, unsafe_allow_html=True)

# --- USER INPUT ---
if user_input := st.chat_input("Tippe oder diktiere hier..."):
    st.session_state.messages.append({"role": "user", "content": user_input})

    # System-Anweisung für das Gespräch
    system_prompt = (
        f"Du bist der Angestellte bei {location}. Stefan antwortet dir. "
        "Antworte ihm immer in diesem Format:\n"
        "STEFAN SAGTE (DEUTSCH): [Deine Vermutung was er meinte]\n"
        "JAPANISCH: [Deine Antwort auf Japanisch]\n"
        "DEUTSCH: [Die Übersetzung deiner Antwort]\n\n"
        "Sei charmant, frech und korrigiere seine Fehler so, wie man einen Schüler "
        "korrigiert, der 2+2=5 gerechnet hat."
    )

    model = genai.GenerativeModel(model_id)
    try:
        response = model.generate_content(f"{system_prompt}\nStefan: {user_input}")
        st.session_state.messages.append({"role": "assistant", "content": response.text})
        st.rerun()
    except Exception as e:
        st.error(f"Fehler: {e}")

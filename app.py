import streamlit as st
from transformers import VitsModel, AutoTokenizer
import torch
import scipy.io.wavfile
import tempfile
import os
import base64
from datetime import datetime
import json
import speech_recognition as sr
import requests
from smolagents import OpenAIServerModel, ToolCallingAgent, Tool

# Disable TensorFlow oneDNN optimizations to suppress warnings
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# Patch Streamlit's file watcher to handle PyTorch compatibility issues
try:
    import streamlit.watcher.local_sources_watcher

    def patched_get_module_paths(module):
        try:
            # Attempt to get module paths safely
            paths = []
            if hasattr(module, '__path__'):
                for path in module.__path__:
                    paths.append(path)
            return paths
        except Exception:
            return []

    # Replace the original get_module_paths function
    streamlit.watcher.local_sources_watcher.get_module_paths = patched_get_module_paths
except ImportError:
    # If the module is not available, skip patching (for newer Streamlit versions)
    pass

# Initialize the TTS model and tokenizer globally
try:
    model_tts = VitsModel.from_pretrained("facebook/mms-tts-ara")
    tokenizer_tts = AutoTokenizer.from_pretrained("facebook/mms-tts-ara")
except Exception as e:
    st.error(f"Erreur lors du chargement du modèle TTS: {e}")
    model_tts = None
    tokenizer_tts = None

# Initialize speech recognizer
recognizer = sr.Recognizer()

# Initialize the AI model for responses
try:
    model_ai = OpenAIServerModel(
        model_id="gemini-2.0-flash",
        api_base="https://generativelanguage.googleapis.com/v1beta",
        api_key=os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY"),  # Replace with valid key
    )
except Exception as e:
    st.error(f"Erreur lors de l'initialisation du modèle Gemini: {e}")
    model_ai = None

# Define the SearchWebTool
class SearchWebTool(Tool):
    name = "moroccan_darija_web_search"
    description = "كيقلب فالمواقع المغربية على الوثائق اللي كيتطلبو فالإدارات بالدارجة المغربية."
    inputs = {
        "query": {
            "type": "string",
            "description": "شنو بغيتي تقلب عليه، مثلا: 'شنو خاصني نوجد لجواز السفر المغرب'"
        }
    }
    output_type = "string"

    def forward(self, query: str) -> str:
        try:
            api_key = os.getenv("SERPAPI_KEY", "YOUR_SERPAPI_KEY")  # Replace with valid key
            response = requests.get(
                "https://serpapi.com/search",
                params={
                    "q": query,
                    "hl": "ar",  # Interface language: Arabic
                    "gl": "ma",  # Country: Morocco
                    "engine": "google",
                    "api_key": api_key
                }
            )
            data = response.json()
            results = data.get("organic_results", [])[:3]
            if not results:
                return "ما لقيتش نتائج دابا، جرب تسول بطريقة أخرى."
            return "\n\n".join(f"{r['title']}\n{r['link']}" for r in results)
        except Exception as e:
            return f"خطأ فالبحث: {str(e)}"

# Initialize the agent
agent = None
if model_ai:
    try:
        agent = ToolCallingAgent(model=model_ai, tools=[SearchWebTool()])
    except Exception as e:
        st.error(f"Erreur lors de l'initialisation de l'agent: {e}")

# Page configuration
st.set_page_config(
    page_title="المقدم",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def init_session():
    if 'conversation' not in st.session_state:
        st.session_state.conversation = []
    if 'audio_enabled' not in st.session_state:
        st.session_state.audio_enabled = True
    if 'recording' not in st.session_state:
        st.session_state.recording = False
    if 'audio_data' not in st.session_state:
        st.session_state.audio_data = None

# Text-to-speech function
def text_to_speech(text):
    if not model_tts or not tokenizer_tts:
        return None
    try:
        inputs = tokenizer_tts(text, return_tensors="pt")
        torch.manual_seed(42)
        with torch.no_grad():
            output = model_tts(**inputs).waveform
        sampling_rate = getattr(model_tts.config, "sampling_rate", 16000)
        audio = output.squeeze().cpu().numpy()
        fp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        scipy.io.wavfile.write(fp.name, rate=sampling_rate, data=audio)
        return fp.name
    except Exception as e:
        st.error(f"Erreur lors de la génération audio: {e}")
        return None

# Read audio file and convert to base64
def get_audio_bytes(audio_file):
    with open(audio_file, 'rb') as f:
        return base64.b64encode(f.read()).decode()

# Convert base64 audio to WAV file
def base64_to_wav(base64_string):
    try:
        audio_data = base64.b64decode(base64_string.split(',')[1])
        fp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        with open(fp.name, 'wb') as f:
            f.write(audio_data)
        return fp.name
    except Exception as e:
        st.error(f"Erreur lors de la conversion de l'audio: {e}")
        return None

# Recognize speech from audio
def recognize_speech(audio_file):
    try:
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language="ar-SA")  # Arabic speech recognition
        return text
    except sr.UnknownValueError:
        st.error("Impossible de comprendre l'audio.")
        return None
    except sr.RequestError as e:
        st.error(f"Erreur lors de la reconnaissance vocale: {e}")
        return None

# AI response function
def get_ai_response(message, model_type="gemini-2.0-flash"):
    if not agent:
        return "Erreur: l'agent IA n'est pas initialisé."
    try:
        # Build conversation string from session state
        conversation = "\n".join(f"{role}: {msg}" for role, msg, _ in st.session_state.conversation) + f"\nUser: {message}\nAssistant:"
        
        # Get response from the agent
        result = agent.run(conversation)
        
        return result
    except Exception as e:
        return f"خطأ في الحصول على الجواب: {str(e)}"

# Main interface
def main():
    init_session()
    
    # Header
    st.title("🤖 مقدمLM")
    st.markdown("---")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Model selection (for UI consistency, using Gemini internally)
        model_choice = st.selectbox(
            "Modèle IA:",
            ["GPT-3.5", "GPT-4", "Claude", "Gemini"],
            index=3  # Default to Gemini
        )
        
        # Audio configuration
        st.subheader("🔊 Audio")
        audio_output = st.checkbox("Sortie audio", value=True)
        audio_input = st.checkbox("Entrée audio", value=False)
        
        # Clear history button
        if st.button("🗑️ Effacer l'historique"):
            st.session_state.conversation = []
            st.rerun()
    
    # Conversation area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.subheader("💬 Conversation")
        
        # Display conversation history
        chat_container = st.container()
        with chat_container:
            for i, (role, message, timestamp) in enumerate(st.session_state.conversation):
                if role == "user":
                    st.markdown(f"**Vous** ({timestamp}):", dir="rtl")
                    st.markdown(f"*{message}*", dir="rtl")
                else:
                    st.markdown(f"**Agent IA** ({timestamp}):", dir="rtl")
                    st.markdown(message, dir="rtl")
                    
                    # Audio button for AI responses
                    if audio_output:
                        if st.button(f"🔊 Écouter", key=f"audio_{i}"):
                            audio_file = text_to_speech(message)
                            if audio_file:
                                audio_bytes = get_audio_bytes(audio_file)
                                st.markdown(f"""
                                <audio controls autoplay>
                                    <source src="data:audio/wav;base64,{audio_bytes}" type="audio/wav">
                                </audio>
                                """, unsafe_allow_html=True)
                                os.unlink(audio_file)  # Clean up temporary file
                
                st.markdown("---")
    
    with col2:
        st.subheader("📊 Statistiques")
        st.metric("Messages", len(st.session_state.conversation))
        st.metric("Modèle actuel", model_choice)
        
        # Export conversation
        if st.button("📥 Exporter"):
            conversation_json = json.dumps(st.session_state.conversation, indent=2, ensure_ascii=False)
            st.download_button(
                label="Télécharger JSON",
                data=conversation_json,
                file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # Input area
    st.markdown("---")
    st.subheader("✍️ Votre message")
    
    # Input methods
    input_method = st.radio("Méthode de saisie:", ["Texte", "Audio"], horizontal=True, dir="rtl")
    
    if input_method == "Texte":
        user_input = st.text_area("Tapez votre message:", height=100, placeholder="Écrivez votre message ici...", dir="rtl")
        
        col_send1, col_send2 = st.columns([1, 4])
        with col_send1:
            send_button = st.button("📤 Envoyer", type="primary")
        
        if send_button and user_input.strip():
            # Add user message
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.conversation.append(("user", user_input, timestamp))
            
            # Generate AI response
            with st.spinner("L'agent réfléchit..."):
                ai_response = get_ai_response(user_input, model_choice)
                st.session_state.conversation.append(("ai", ai_response, timestamp))
            
            st.rerun()
    
    else:  # Audio input
        st.info("🎤 Enregistrement audio")
        # JavaScript for audio recording
        st.markdown("""
        <script>
        let mediaRecorder;
        let audioChunks = [];

        async function startRecording() {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder = new MediaRecorder(stream);
            audioChunks = [];
            
            mediaRecorder.ondataavailable = e => {
                audioChunks.push(e.data);
            };
            
            mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                const reader = new FileReader();
                reader.readAsDataURL(audioBlob);
                reader.onloadend = () => {
                    const base64String = reader.result;
                    document.getElementById('audio_data').value = base64String;
                    document.getElementById('audio_form').submit();
                };
            };
            
            mediaRecorder.start();
            document.getElementById('record_button').innerText = 'Arrêter l\'enregistrement';
            document.getElementById('record_button').onclick = stopRecording;
        }

        function stopRecording() {
            mediaRecorder.stop();
            document.getElementById('record_button').innerText = 'Démarrer l\'enregistrement';
            document.getElementById('record_button').onclick = startRecording;
        }
        </script>

        <button id="record_button" onclick="startRecording()">Démarrer l'enregistrement</button>
        <form id="audio_form" style="display: none;">
            <input type="hidden" id="audio_data" name="audio_data">
        </form>
        """, unsafe_allow_html=True)
        
        # Capture audio data from JavaScript
        audio_data = st.experimental_get_query_params().get("audio_data", [None])[0]
        
        if audio_data:
            audio_file = base64_to_wav(audio_data)
            if audio_file:
                st.audio(audio_file, format="audio/wav")
                if st.button("🎯 Traiter l'audio"):
                    with st.spinner("Traitement de l'audio..."):
                        text = recognize_speech(audio_file)
                        if text:
                            timestamp = datetime.now().strftime("%H:%M:%S")
                            st.session_state.conversation.append(("user", text, timestamp))
                            with st.spinner("L'agent réfléchit..."):
                                ai_response = get_ai_response(text, model_choice)
                                st.session_state.conversation.append(("ai", ai_response, timestamp))
                            st.experimental_set_query_params()  # Clear query params
                            os.unlink(audio_file)  # Clean up
                            st.rerun()
                        else:
                            os.unlink(audio_file)
    
    # Information section
    with st.expander("ℹ️ Informations sur l'agent"):
        st.markdown("""
        ### Fonctionnalités disponibles:
        - **Conversation textuelle** avec un modèle IA en Darija marocaine (Gemini avec recherche web)
        - **Synthèse vocale** pour les réponses (arabe via MMS-TTS)
        - **Enregistrement et reconnaissance vocale** pour l'entrée audio
        - **Historique** de conversation
        - **Export** des conversations
        - **Configuration** personnalisable
        
        ### Pour une utilisation complète:
        1. Installez les dépendances :
           ```bash
           pip install streamlit transformers torch scipy speechrecognition smolagents requests pyaudio
           ```
        2. Configurez les clés API via des variables d'environnement :
           ```powershell
           $env:GEMINI_API_KEY = "your_gemini_api_key"
           $env:SERPAPI_KEY = "your_serpapi_key"
           ```
        3. Assurez-vous que `pyaudio` est installé (peut nécessiter des dépendances système, comme `portaudio` sur Windows).
        
        ### Modèles supportés:
        - Gemini (Google) avec outil de recherche web pour Darija
        - MMS-TTS (Hugging Face) pour la synthèse vocale en arabe
        - Google Speech Recognition pour l'entrée vocale
        """)

if __name__ == "__main__":
    main()

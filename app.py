import streamlit as st
# from transformers import VitsModel, AutoTokenizer
# import torch
# import scipy.io.wavfile
# import tempfile
import os
# import base64
from datetime import datetime
import json
# import speech_recognition as sr
import requests
from smolagents import OpenAIServerModel, ToolCallingAgent, Tool

# os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

# try:
#     import streamlit.watcher.local_sources_watcher
#     def patched_get_module_paths(module):
#         try:
#             if hasattr(module, '_path_'):
#                 return list(module._path_)
#             return []
#         except Exception:
#             return []
#     streamlit.watcher.local_sources_watcher.get_module_paths = patched_get_module_paths
# except ImportError:
#     pass

# Initialiser modèle IA Gemini
try:
    model_ai = OpenAIServerModel(
        model_id="gemini-2.0-flash",
        api_base="https://generativelanguage.googleapis.com/v1beta",
        api_key="AIzaSyAGzTxntsUg-C2Mu1tCIDNqgT1Q1loxo64"
    )
except Exception as e:
    st.error(f"Erreur initialisation modèle Gemini: {e}")
    model_ai = None

# Définir l'outil de recherche web
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
            api_key ="59987dee629e60fa56510999efde2faecac8beee73bcab5ad1fcea0b6d1244e8"
            response = requests.get(
                "https://serpapi.com/search",
                params={"q": query, "hl": "ar", "gl": "ma", "engine": "google", "api_key": api_key}
            )
            data = response.json()
            results = data.get("organic_results", [])[:3]
            if not results:
                return "ما لقيتش نتائج دابا، جرب تسول بطريقة أخرى."
            return "\n\n".join(f"{r['title']}\n{r['link']}" for r in results)
        except Exception as e:
            return f"خطأ فالبحث: {str(e)}"

# Agent IA
agent = None
if model_ai:
    try:
        agent = ToolCallingAgent(model=model_ai, tools=[SearchWebTool()])
    except Exception as e:
        st.error(f"Erreur initialisation agent: {e}")

# Config page
st.set_page_config(
    page_title="المقدم",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session():
    for key in ['conversation', 'audio_enabled', 'recording', 'audio_data']:
        if key not in st.session_state:
            st.session_state[key] = [] if key == 'conversation' else None if key == 'audio_data' else False

# def text_to_speech(text):
#     ...

# def get_audio_bytes(audio_file):
#     ...

# def base64_to_wav(base64_string):
#     ...

# def recognize_speech(audio_file):
#     ...

def get_ai_response(message, model_type="gemini-2.0-flash"):
    if not agent:
        return "Erreur: agent IA non initialisé."
    try:
        conversation = "\n".join(f"{role}: {msg}" for role, msg, _ in st.session_state.conversation)
        result = agent.run(f"{conversation}\nUser: {message}\nAssistant:")
        return result
    except Exception as e:
        return f"خطأ في الحصول على الجواب: {str(e)}"

def main():
    init_session()

    # 🔧 CSS Style
    st.markdown("""
        <style>
        .message-user {
            background-color: #690273;
            padding: 12px;
            border-radius: 12px;
            margin-bottom: 10px;
            text-align: right;
            font-family: 'Segoe UI', sans-serif;
            direction: rtl;
        }
        .message-ai {
            background-color: #060270;
            padding: 12px;
            border-radius: 12px;
            margin-bottom: 10px;
            text-align: left;
            font-family: 'Courier New', monospace;
        }
        .timestamp {
            font-size: 0.8em;
            color: gray;
            margin-bottom: 4px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("🤖 مقدم ML")
    st.markdown("---")

    # 🛠 Barre latérale
    with st.sidebar:
        st.header("⚙ Configuration")
        model_choice = st.selectbox("Modèle IA:", ["مقدم ML", "الباشا"], index=0)
        if st.button("🗑 Effacer l'historique"):
            st.session_state.conversation = []
            st.rerun()

    # 💬 Affichage des messages
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader("💬 Conversation")
        for i, (role, message, timestamp) in enumerate(st.session_state.conversation):
            role_class = "message-user" if role == "user" else "message-ai"
            name = "🧑‍💻 أنت" if role == "user" else "🤖 LM مقدم"
            html = f'''
            <div class="{role_class}">
                <div class="timestamp">{name} • {timestamp}</div>
                {message}
            </div>
            '''
            st.markdown(html,unsafe_allow_html=True)

    # 📊 Stats
    with col2:
        st.metric("Messages", len(st.session_state.conversation))
        st.metric("Modèle actuel", model_choice)
        if st.button("📥 Exporter"):
            json_data = json.dumps(st.session_state.conversation, indent=2, ensure_ascii=False)
            st.download_button("Télécharger JSON", data=json_data, file_name="conversation.json", mime="application/json")

    st.markdown("---")
    st.subheader("✍ Votre message")
    input_method = st.radio("Méthode de saisie:", ["Texte"], horizontal=True, key="input_mode")

    if st.session_state.input_mode == "Texte":
        user_input = st.text_area("Tapez votre message:", height=100, placeholder="Écrivez ici...")
        if st.button("📤 Envoyer") and user_input.strip():
            timestamp = datetime.now().strftime("%H:%M:%S")
            st.session_state.conversation.append(("user", user_input, timestamp))
            with st.spinner("LM مقدم réfléchit..."):
                ai_response = get_ai_response(user_input, model_choice)
                st.session_state.conversation.append(("ai", ai_response, timestamp))
            st.rerun()

    with st.expander("ℹ Informations sur LM مقدم"):
        st.markdown("""
        ### Fonctionnalités:
        - الدردشة بالدارجة المغربية
        - البحث فالويب
        - تقديم توجيه لقضاء المهام الادارية
        """)

if __name__ == "__main__":
    main()
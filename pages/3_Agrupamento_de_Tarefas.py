# pages/3_Agrupamento_de_Tarefas.py
import streamlit as st
from utils import Storage, generate_audio_from_text

st.set_page_config(layout="wide")
if 'storage' not in st.session_state:
    st.session_state.storage = Storage()
storage = st.session_state.storage

st.header("📦 Agrupamento de Tarefas com IA (Google Gemini)")
st.markdown("Esta ferramenta usa a IA do Google Gemini para analisar o significado das suas tarefas e agrupá-las por similaridade.")
api_key = st.text_input("🔑 Chave de API do Google AI", type="password", help="Sua chave será lida do arquivo secrets.toml", value=st.secrets.get("GOOGLE_API_KEY", ""))

if not api_key:
    st.warning("Por favor, adicione sua chave de API do Google AI no arquivo .streamlit/secrets.toml")
else:
    if st.button("Agrupar Tarefas com IA"):
        with st.spinner("Analisando e agrupando suas tarefas..."):
            task_groups = storage.group_tasks_by_similarity_ai(api_key=api_key)
            st.session_state.task_groups = task_groups 
if 'task_groups' in st.session_state and st.session_state.task_groups:
    task_groups = st.session_state.task_groups
    st.success(f"Encontramos {len(task_groups)} grupo(s) de tarefas similares!")
    
    if st.button("🔊 Ler Resumo dos Grupos"):
        tld = st.session_state.get('tts_tld', 'com.br')
        slow = st.session_state.get('tts_slow', False)
        summary_text = f"Encontrei {len(task_groups)} grupos de tarefas. "
        for i, group in enumerate(task_groups, start=1):
            summary_text += f"O grupo {i} parece ser sobre {group[0]['title']} e contém {len(group)} tarefas. "
        with st.spinner("Gerando áudio..."):
            audio_buffer = generate_audio_from_text(summary_text, tld=tld, slow=slow)
            if audio_buffer:
                st.audio(audio_buffer, format='audio/mp3')
            else:
                st.error("Não foi possível gerar o áudio.")
    for i, group in enumerate(task_groups, start=1):
        with st.expander(f"Grupo {i} - {len(group)} tarefas relacionadas"):
            for task in group:
                st.markdown(f"**- {task['title']}**")
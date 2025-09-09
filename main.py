# main.py
import streamlit as st
from pathlib import Path
from utils import Storage, generate_audio_from_text

APP_TITLE = "Painel de Produtividade"
st.set_page_config(page_title=APP_TITLE, page_icon="🚀", layout="wide")

if 'storage' not in st.session_state:
    st.session_state.storage = Storage()
storage = st.session_state.storage

st.title(APP_TITLE)
st.markdown("Bem-vindo à sua central de produtividade. Use o menu à esquerda para navegar entre as ferramentas.")

with st.sidebar:
    st.header("Configurações Gerais")
    if st.button("⚠️ Resetar todas as tarefas"):
        storage.reset()
        st.success("Dados resetados.")
        st.rerun()
    st.markdown("---")
    st.header("Opções de Voz")
    accents = {"Português (Brasil)": "com.br", "Português (Portugal)": "pt"}
    selected_accent_label = st.selectbox("Sotaque da Voz:", options=list(accents.keys()))
    st.session_state.tts_tld = accents[selected_accent_label]
    st.session_state.tts_slow = st.toggle("Fala Lenta", value=False)

st.header("⚡ Urgências do Dia")
urgent_tasks = storage.get_urgent_tasks()

if st.button("🔊 Ouvir Resumo do Dia"):
    tld = st.session_state.get('tts_tld', 'com.br')
    slow = st.session_state.get('tts_slow', False)
    if not urgent_tasks:
        summary_text = "Ótima notícia! Você não tem nenhuma tarefa urgente para hoje. Bom trabalho!"
    else:
        num_tasks = len(urgent_tasks)
        plural = 's' if num_tasks > 1 else ''
        summary_text = f"Olá! Você tem {num_tasks} tarefa{plural} urgente{plural} para hoje. São elas: "
        for i, task in enumerate(urgent_tasks, start=1):
            summary_text += f"{i}. {task['title']}. "
    with st.spinner("Gerando seu resumo em áudio..."):
        audio_buffer = generate_audio_from_text(summary_text, tld=tld, slow=slow)
        if audio_buffer:
            st.audio(audio_buffer, format='audio/mp3')
        else:
            st.error("Desculpe, não foi possível gerar o áudio.")

if not urgent_tasks:
    st.success("Nenhuma tarefa urgente para hoje. Bom trabalho!")
else:
    for task in urgent_tasks:
        is_done = task.get('status') == 'done'
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            st.markdown(f"**{task['title']}**")
            if task.get('description'):
                st.caption(task['description'])
        with col2:
            if st.checkbox("✔", value=is_done, key=f"done_main_{task['id']}", help="Marcar como concluída"):
                if not is_done:
                    storage.mark_done(task['id'])
                    st.rerun()
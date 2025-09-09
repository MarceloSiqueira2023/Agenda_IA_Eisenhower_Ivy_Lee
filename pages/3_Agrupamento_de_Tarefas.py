import streamlit as st
from utils import Storage, generate_audio_from_text

st.set_page_config(layout="wide")
st.header("📦 Agrupamento de Tarefas por Categoria")
st.markdown("Veja as suas tarefas organizadas pelas categorias (tags) que você mesmo definiu.")

if 'storage' not in st.session_state:
    st.session_state.storage = Storage()
storage = st.session_state.storage

# Chama a nova função de agrupamento por tag
grouped_tasks = storage.group_tasks_by_tag()

if not grouped_tasks:
    st.info("Nenhuma tarefa pendente com tags foi encontrada. Adicione tags às suas tarefas na Matriz de Eisenhower para as ver agrupadas aqui.")
else:
    # Botão para ler o resumo dos grupos
    if st.button("🔊 Ler Resumo dos Grupos"):
        summary_text = f"Encontrei {len(grouped_tasks)} grupos de tarefas. "
        for tag, tasks in grouped_tasks.items():
            plural = "tarefas" if len(tasks) > 1 else "tarefa"
            summary_text += f"Na categoria {tag}, você tem {len(tasks)} {plural}. "
        
        with st.spinner("A gerar áudio..."):
            tld = st.session_state.get('tts_tld', 'com.br')
            slow = st.session_state.get('tts_slow', False)
            audio_buffer = generate_audio_from_text(summary_text, tld=tld, slow=slow)
            if audio_buffer:
                st.audio(audio_buffer, format='audio/mp3')

    # Exibe cada grupo num expander
    for tag, tasks in grouped_tasks.items():
        with st.expander(f"**{tag}** ({len(tasks)} tarefa(s))"):
            for task in tasks:
                is_done = task.get('status') == 'done'
                col1, col2 = st.columns([0.9, 0.1])
                with col1:
                    st.markdown(f"**- {task['title']}**")
                    if task.get('description'):
                        st.caption(task.get('description'))
                with col2:
                    if st.checkbox("✔", value=is_done, key=f"group_done_{task['id']}", help="Marcar como concluída"):
                        if not is_done:
                            storage.mark_done(task['id'])
                            st.rerun()


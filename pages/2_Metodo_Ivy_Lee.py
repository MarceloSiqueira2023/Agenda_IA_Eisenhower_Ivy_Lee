# pages/2_Metodo_Ivy_Lee.py
import streamlit as st
from utils import Storage

st.set_page_config(layout="wide")
if 'storage' not in st.session_state:
    st.session_state.storage = Storage()
storage = st.session_state.storage

st.header("🎯 Método Ivy Lee: As 6 Tarefas Mais Importantes")
st.markdown("Ao final de cada dia, defina as 6 tarefas mais importantes para amanhã. Comece pela primeira e siga a lista em ordem.")
st.info("A lista abaixo é priorizada automaticamente com base na sua Matriz de Eisenhower (Importância > Urgência).")

top_tasks = storage.get_top_n_pending_tasks(n=6)
if not top_tasks:
    st.success("✨ Nenhuma tarefa prioritária pendente! Adicione novas na Matriz de Eisenhower.")
else:
    st.subheader("Sua lista para hoje:")
    for i, task in enumerate(top_tasks, start=1):
        is_done = task.get('status') == 'done'
        st.markdown("---")
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            st.markdown(f"### {i}. {task['title']}")
        with col2:
            if st.checkbox("✔", value=is_done, key=f"ivylee_done_{task['id']}", help="Marcar como concluída"):
                if not is_done:
                    storage.mark_done(task['id'])
                    st.rerun()